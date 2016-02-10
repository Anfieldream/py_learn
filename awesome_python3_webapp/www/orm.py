#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'eric'
import asyncio,logging
logging.basicConfig(level=logging.DEBUG)
import aiomysql

def log(sql,args=()):
    logging.info('SQL: %s' % sql)

#创建连接池
@asyncio.coroutine
def create_pool(loop,**kw):
    logging.info('create database connection pool...')
    #全局变量__pool
    global __pool
    #创建数据库连接池
    __pool = yield from aiomysql.create_pool(
        host = kw.get('host','localhost'),
        port = kw.get('port',3306),
        user = kw['user'],  #user取传入的参数key为user的值
        password = kw['password'],
        db = kw['db'],
        charset = kw.get('charset','utf8'), #编码为utf8
        autocommit = kw.get('autocommit',True), 	#自动提交事务设为开启
        maxsize=kw.get('maxsize',10),   #连接池最多10条连接，默认是10
        minsize=kw.get('minsize',1),    #连接池最少1条连接，默认是10
        loop=loop   #运行loop为传入的loop
    )

#select 语句
@asyncio.coroutine
def select(sql,args,size=None):
    log(sql,args)
    global __pool
    #从连接池取一个conn出来，with..as..会在运行完后把conn放回连接池
    with(yield from __pool) as conn:
        #获取一个cursor，通过aiomysql.DictCursor获取到的cursor在返回结果时会返回一个字典格式
        cur = yield from conn.cursor(aiomysql.DictCursor)
        #把sql语句的'?'替换为'%s',并把args的值填充到相应的位置补充成完整的可执行sql语句并执行，mysql中得占位符是'?'，python中得为'%s'
        yield from cur.execute(sql.replace('?','%s'),args or ())
        #如果有要求的返回行数，则取要求的行数，如果没有，则全部取出
        if size:
            rs = yield from cur.fetchmany(size)
        else:
            rs = yield from cur.fetchall()
        yield from cur.close()  #关闭cursor
        logging.info('rows returned: %s' % len(rs))
        return rs

#insert,update,delete
@asyncio.coroutine
def execute(sql,args):
    log(sql)
    #从连接池取一个conn出来，with..as..会在运行完后把conn放回连接池
    with (yield from __pool) as conn:
        try:
            #获取一个cursor
            cur = yield from conn.cursor()
            yield from cur.execute(sql.replace('?','%s'),args)
            #取出执行结果的条数
            affected = cur.rowcount
            yield from cur.close()
        except BaseException as e:
            raise
        return affected


#构造sql语句参数字符串，最后返回的字符串会以','分割多个'?'，如 num==2，则会返回 '?, ?'
def create_args_string(num):
    L=[]
    for n in range(num):
        L.append('?')
    return ','.join(L)


#用于标识model里每个成员变量的类
#name:名字
#column_type:值类型
#primary_key:是否primary_key
#default:默认值
class Field(object):
    #init函数，在对象new之后初始化的时候自动调用，这里初始化一些成员变量
    def __init__(self,name,column_type,primary_key,default):
        self.name=name
        self.column_type=column_type
        self.primary_key = primary_key
        self.default = default
    #直接打印对象的实现方法
    def __str__(self):
        return '<%s, %s:%s>' %(self.__class__.__name__,self.column_type,self.name)

class StringField(Field):
    def __init__(self,name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(name,ddl,primary_key,default)

class BooleanField(Field):
    def __init__(self, name=None, default=False):
        super().__init__(name,'boolean',False,default)

class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super.__init__(name,'bigint',primary_key,default)

class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name,'real',primary_key,default)

class TextField(Field):
    def __init__(self, name=None, default=None):
        super().__init__(name,'text',False,default)

#model元类，元类可以创建类对象。可以查看这个http://blog.jobbole.com/21351/，了解元类
class ModelMetaclass(type):

    #new函数
	#cls:
	#name:创建的类名
	#bases:父类的数组，可为空， 如果有值的话(则值是生成类的父类），生成的类是继承此数组里的类的
	#attrs:包含属性的字典
    def __new__(cls,name,bases,attrs):          #__new__是在__init__之前被调用的特殊方法，用来创建对象并返回之的方法
        #排除Model类本身
        if name =='Model':
            return type.__new__(cls,name,bases,attrs)
        #Model的子类会继续往下走
        #获取table名称:attrs的'__table__'键对应的value，如果为空的话则用name字段的值
        tableName=attrs.get('__table__',None) or name
        logging.info('found model: %s (table: %s)' % (name,tableName))
        #获取所有Filed和主键名
        mappings=dict()     #mappings字典，存放所有Field键值对，属性名：value
        fields = []     #fields数组，存放除了主键以外的属性名
        primaryKey=None
        for k,v in attrs.items():       #k,v 分别对应创建时传进来的需要赋值的属性名，和要赋的值
            if isinstance(v,Field):     #查看value是不是Field类型，是的话继续
                logging.info('found mapping: %s ==> %s' % (k,v))
                mappings[k]=v           #把符合要求的放到mappings里
                if v.primary_key:       #如果当前Field是主键，则记录下来
                    #找到主键
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field: %s' %k)
                    primaryKey = k      #记录主键
                else:
                    fields.append(k)        #不是主键的话把key值放到fields里
        #如果遍历完后没有主键，抛出错误
        if not primaryKey:
            raise RuntimeError('Primary key not found.')
        #把attrs里除了主键以外的其他键值去掉
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields=list(map(lambda f: '`%s`' % f,fields))       #把fields的值全部加了个 ``
        attrs['__mappings__']=mappings  #保存属性和列的映射关系
        attrs['__table__']=tableName
        attrs['__primary_key__']=primaryKey #主键属性名
        attrs['__fields__']=fields  #除主键外的属性名
        #构造默认的select,insert,update和delete语句
        attrs['__select__']='select `%s`, %s from `%s`' % (primaryKey,','.join(escaped_fields),tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        return type.__new__(cls,name,bases,attrs)

class Model(dict,metaclass=ModelMetaclass):

    def __init__(self,**kw):        #__init__只是用来将传入的参数初始化给对象
        super(Model,self).__init__(**kw)

    #重写访问属性的方法，没有属性和key一样则抛错
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self,key):
        return getattr(self,key,None)

    #访问某个key的方法，如果value是None，则去mappings获取default值
    def getValueOrDefault(self,key):
        value = getattr(self,key,None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' %(key,str(value)))
                setattr(self,key,value)
        return value

    #查询所有，可以设定查询顺序'order by', 查询条数'limit'
    @classmethod
    @asyncio.coroutine
    def findAll(cls, where=None, args=None, **kw):
        'find objects by where clause.'
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args=[]
        orderBy = kw.get('orderBy',None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit',None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit,int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit,tuple) and len(limit) == 2:
                sql.append('?,?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' %str(limit))
        rs = yield from select(' '.join(sql),args)
        return [cls(**r) for r in rs]

    #查询某个条件下的数据有多少条
    @classmethod
    @asyncio.coroutine
    def findNumber(cls,selectField,where=None,args=None):
        'find number by select and where.'
        sql = ['select %s __num__ from `%s`' % (selectField,cls.__table)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = yield from select(' '.join(sql),args,1)
        if len(rs) == 0:
            return None
        return rs[0]['__num__']

    #根据主键查找pk的值，取第一条
    @classmethod
    @asyncio.coroutine
    def find(cls,pk):
        'find object by primary key.'
        rs = yield from select('%s where `%s`=?' % (cls.__select__,cls.__primary_key__),[pk],1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    #根据当前类的属性，往相关table里插入一条数据
    @asyncio.coroutine
    def save(self):
        args = list(map(self.getValueOrDefault,self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = yield from execute(self.__insert__,args)
        if rows != 1:
            logging.warning('failed to insert record:affected rows: %s' % rows)

    #更新条目数据
    @asyncio.coroutine
    def update(self):
        args = list(map(self.getValue,self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = yield from execute(self.__update__,args)
        if rows != 1:
            logging.warning('failed to update by primary key: affected rows: %s' % rows)

    #根据主键的值删除条目
    @asyncio.coroutine
    def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = yield from execute(self.__delete__,args)
        if rows != 1:
            logging.warning('failed to remove by primary key: affected rows: %s' % rows)