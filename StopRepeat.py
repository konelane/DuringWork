#! /usr/bin/env python3
# coding:utf-8
from datetime import datetime
import sqlite3
from os.path import basename

from core.decos import DisableModule, check_group, check_member, check_permitGroup
from core.MessageProcesser import MessageProcesser
from core.ModuleRegister import Module
from database.kaltsitReply import blockList
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain
from graia.ariadne.message.parser.twilight import RegexMatch, Twilight
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

channel = Channel.current()

module_name = basename(__file__)[:-3]

Module(
    name='StopRepeat',
    file_name=module_name,
    author=['KOneLane'],
    usage='modules.StopRepeat',
).register()


class stopRepeatQueue:
    def __init__(self, msg) -> None:
        self.msg = msg
        self.filename = './bot/database/'
        self.groupId = str(msg['group_id'])
        self.pub_time = datetime.now()
        pass


    def databaseInit(self):
        """给当前群建表"""
        con,cur = self.__connectSqlite()
        cur.execute(f"CREATE TABLE IF NOT EXISTS `{self.groupId}_text` (pub_time TEXT PRIMARY KEY NOT NULL, text TEXT, pub_id TEXT)")
        con.commit()# 事务提交，保存修改内容。
        con.close()
        cur.execute(f"REPLACE INTO '{self.groupId}_text' (pub_time, text, pub_id) VALUES(?,?,?)",(
            'header', 'good', '123456789'
            )
        )
        self.__dataSave() # 保存消息内容




    def __connectSqlite(self):
        """连接数据库"""
        con = sqlite3.connect(self.filename + 'Kal-tsit.db')
        cur = con.cursor()
        return (con,cur)


    def __dataSave(self):
        """存数据"""
        con,cur = self.__connectSqlite()
        cur.execute(f"REPLACE INTO '{self.groupId}_text' (pub_time, text, pub_id) VALUES(?,?,?)",(
            self.pub_time, self.msg['text_ori'], self.msg['id']
            )
        )
        con.commit()# 事务提交，保存修改内容。
        con.close()


    def __checkData(self):
        """消息-查询-检查"""
        con,cur = self.__connectSqlite()
        cur.execute(f"SELECT COUNT(*) FROM '{self.groupId}_text'")
        linescheck = cur.fetchall()[0][0]
        # print(linescheck)
        if linescheck <= 10:
            return False
        else:
            cur.execute(f"SELECT text FROM (SELECT * FROM '{self.groupId}_text' ORDER BY pub_time desc LIMIT 5)")
            # print(cur.fetchall())
            temp = list(set(list(cur.fetchall())))
            # print(temp) # [('凯尔希不能发图了草',), ('哭了',), ('哈哈哈',)]
            con.close()
            if len(temp) == 1 and temp[0][0] == self.msg['text_ori']:
                return True
            else:
                return False

    def checkTables(self):
        con,cur = self.__connectSqlite()
        # cur.execute(f"SELECT ObjectProperty(Object_ID('{self.groupId}_text'),'IsUserTable')")
        # cur.execute(f"SELECT COUNT(1) FROM sys.objects WHERE name = '{self.groupId}_text'")
        cur.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name = '{self.groupId}_text'")
        check_result = list(cur.fetchall()[0])[0]
        return check_result


    def activeRun(self):
        """检查-选择操作-保存"""
        self.__dataSave()
        if self.__checkData():
            # 复读触发，发图，清理数据
            con,cur = self.__connectSqlite()
            cur.execute(f"DELETE FROM '{self.groupId}_text' WHERE text in(SELECT `text` FROM '{self.groupId}_text' ORDER BY pub_time desc LIMIT 4)") # 删除最后相同的数据
            con.commit()# 事务提交，保存修改内容。
            con.close()
            
            return '咳咳'
        else:
            # 保存新数据
            
        
            return 



@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        # inline_dispatchers=[Twilight([RegexMatch(r'#sc')])],
        decorators=[check_group(blockList.blockGroup), check_member(blockList.blockID), check_permitGroup(blockList.permitGroup), DisableModule.require(module_name)],
    )
)
async def StopRepeat_inGroup(
    app: Ariadne, 
    group: Group, 
    message: MessageChain,
    member: Member
):
    # 复读打断功能
    slightly_inittext = MessageProcesser(message, group, member)
    msg_info_dict = slightly_inittext.text_processer()   
    if msg_info_dict != '':
        test = stopRepeatQueue(msg_info_dict)
        check_table_if_exist = test.checkTables() # 1和0
        
        if check_table_if_exist != 0:
            # print(test.activeRun())
            temp_text = test.activeRun()
            if not temp_text:
                pass
            elif temp_text == '咳咳':
                await app.send_group_message(group, MessageChain([
                    Image(path = './bot/database/faces/stopRepeat.jpg')
                    # Image(url = 'https://m1.im5i.com/2021/11/19/Un5Qhf.jpg')
                ]))
        else:
            test.databaseInit()