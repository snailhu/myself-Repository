__author__ = 'robin'

from thrift.transport import TSocket

from hbase import Hbase
from hbase.ttypes import *

transport = TSocket.TSocket('192.168.1.241', 9090)

transport = TTransport.TBufferedTransport(transport)

protocol = TBinaryProtocol.TBinaryProtocol(transport)

client = Hbase.Client(protocol)
transport.open()

# create table
# contents = ColumnDescriptor(name='cf:', maxVersions=1)
# client.createTable('test', [contents])
tableNames = client.getTableNames()
print client.getTableNames()