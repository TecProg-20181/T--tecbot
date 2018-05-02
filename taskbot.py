#!/usr/bin/env python3

import json
import requests
import time
import urllib

import sqlalchemy

import db
from db import Task

TOKEN = open("token.txt", 'r')
URL = "https://api.telegram.org/bot{}/".format(TOKEN.read())

HELP = """
 /new NOME
 /todo ID
 /doing ID
 /done ID
 /delete ID
 /list
 /rename ID NOME
 /dependson ID ID...
 /duplicate ID
 /setPriority ID PRIORITY{low, medium, high}
 /showPriority 
 /help
"""


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js


def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))

    return max(update_ids)


def deps_text(task, chat, preceed=''):
    text = ''

    for i in range(len(task.dependencies.split(',')[:-1])):
        line = preceed
        query = db.session.query(Task).filter_by(id=int(task.dependencies.split(',')[:-1][i]), chat=chat)
        dep = query.one()

        icon = '\U0001F195'
        if dep.status == 'DOING':
            icon = '\U000023FA'
        elif dep.status == 'DONE':
            icon = '\U00002611'

        if i + 1 == len(task.dependencies.split(',')[:-1]):
            line += '└── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
            line += deps_text(dep, chat, preceed + '    ')
        else:
            line += '├── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
            line += deps_text(dep, chat, preceed + '│   ')

        text += line

    return text


def printTasks(query, chat, message):
    for task in query.all():
        icon = '\U0001F195'
        if task.status == 'DOING':
            icon = '\U000023FA'
        elif task.status == 'DONE':
            icon = '\U00002611'
        message += '[[{}]] {} {} _{}_\n'.format(task.id, icon, task.name, task.priority)
        message += deps_text(task, chat)
    return message

def list(chat):
    query = db.session.query(Task).filter_by(parents='', chat=chat).order_by(Task.id)
    queryTODO = db.session.query(Task).filter_by(status='TODO', chat=chat).order_by(Task.id)
    queryDOING = db.session.query(Task).filter_by(status='DOING', chat=chat).order_by(Task.id)
    queryDONE = db.session.query(Task).filter_by(status='DONE', chat=chat).order_by(Task.id)

    a = ''
    a += '\U0001F4CB Task List\n'
    a = printTasks(query, chat, a)
    send_message(a, chat)
    a = ''
    a += '\U0001F4DD _Status_\n'
    a += '\n\U0001F195 *TODO*\n'
    a = printTasks(queryTODO, chat, a)
    a += '\n\U000023FA *DOING*\n'
    a = printTasks(queryDOING, chat, a)
    a += '\n\U00002611 *DONE*\n'
    a = printTasks(queryDONE, chat, a)
    send_message(a, chat)


def showPriority(chat):
    queryHigh = db.session.query(Task).filter_by(parents='', chat=chat, priority='high').order_by(Task.id)
    queryMedium = db.session.query(Task).filter_by(parents='', chat=chat, priority='medium').order_by(Task.id)
    queryLow = db.session.query(Task).filter_by(parents='', chat=chat, priority='low').order_by(Task.id)
    query = db.session.query(Task).filter_by(parents='', chat=chat, priority='').order_by(Task.id)

    queryHighTODO = db.session.query(Task).filter_by(status='TODO', parents='', chat=chat,
                                                     priority='high').order_by(Task.id)
    queryMediumTODO = db.session.query(Task).filter_by(status='TODO', parents='', chat=chat,
                                                       priority='medium').order_by(Task.id)
    queryLowTODO = db.session.query(Task).filter_by(status='TODO', parents='', chat=chat,
                                                    priority='low').order_by(Task.id)
    queryTODO = db.session.query(Task).filter_by(status='TODO', parents='', chat=chat, priority='').order_by(
        Task.id)

    queryHighDOING = db.session.query(Task).filter_by(status='DOING', parents='', chat=chat,
                                                      priority='high').order_by(Task.id)
    queryMediumDOING = db.session.query(Task).filter_by(status='DOING', parents='', chat=chat,
                                                        priority='medium').order_by(Task.id)
    queryLowDOING = db.session.query(Task).filter_by(status='DOING', parents='', chat=chat,
                                                     priority='low').order_by(Task.id)
    queryDOING = db.session.query(Task).filter_by(status='DOING', parents='', chat=chat, priority='').order_by(
        Task.id)

    queryHighDONE = db.session.query(Task).filter_by(status='DONE', parents='', chat=chat,
                                                     priority='high').order_by(Task.id)
    queryMediumDONE = db.session.query(Task).filter_by(status='DONE', parents='', chat=chat,
                                                       priority='medium').order_by(Task.id)
    queryLowDONE = db.session.query(Task).filter_by(status='DONE', parents='', chat=chat,
                                                    priority='low').order_by(Task.id)
    queryDONE = db.session.query(Task).filter_by(status='DONE', parents='', chat=chat, priority='').order_by(
        Task.id)

    a = ''
    a += '\U0001F4CB Task List\n'
    a = printTasks(queryHigh, chat, a)
    a = printTasks(queryMedium, chat, a)
    a = printTasks(queryLow, chat, a)
    a = printTasks(query, chat, a)
    send_message(a, chat)

    a = ''
    a += '\U0001F4DD _Status_\n'
    a += '\n\U0001F195 *TODO*\n'
    a = printTasks(queryHighTODO, chat, a)
    a = printTasks(queryMediumTODO, chat, a)
    a = printTasks(queryLowTODO, chat, a)
    a = printTasks(queryTODO, chat, a)
    a += '\n\U000023FA *DOING*\n'
    a = printTasks(queryHighDOING, chat, a)
    a = printTasks(queryMediumDOING, chat, a)
    a = printTasks(queryLowDOING, chat, a)
    a = printTasks(queryDOING, chat, a)
    a += '\n\U00002611 *DONE*\n'
    a = printTasks(queryHighDONE, chat, a)
    a = printTasks(queryMediumDONE, chat, a)
    a = printTasks(queryLowDONE, chat, a)
    a = printTasks(queryDONE, chat, a)
    send_message(a, chat)


def creteNewTask(chat, msg):
    task = Task(chat=chat, name=msg, status='TODO', dependencies='', parents='', priority='')
    db.session.add(task)
    db.session.commit()
    send_message("New task *TODO* [[{}]] {}".format(task.id, task.name), chat)

def renameTask(msg, chat):
    text = ''
    if msg != '':
        if len(msg.split(' ', 1)) > 1:
            text = msg.split(' ', 1)[1]
        msg = msg.split(' ', 1)[0]

    if not msg.isdigit():
        send_message("You must inform the task id", chat)
    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return

        if text == '':
            send_message("You want to modify task {}, but you didn't provide any new text".format(task_id),
                         chat)
            return

        old_text = task.name
        task.name = text
        db.session.commit()
        send_message("Task {} redefined from {} to {}".format(task_id, old_text, text), chat)

def createDuplicate(msg, chat):
    if not msg.isdigit():
        send_message("You must inform the task id", chat)
    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return

        dtask = Task(chat=task.chat, name=task.name, status=task.status, dependencies=task.dependencies,
                     parents=task.parents, priority=task.priority, duedate=task.duedate)
        db.session.add(dtask)

        for t in task.dependencies.split(',')[:-1]:
            qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
            t = qy.one()
            t.parents += '{},'.format(dtask.id)

        db.session.commit()
        send_message("New task *TODO* [[{}]] {}".format(dtask.id, dtask.name), chat)

def deleteTask(msg, chat):
    if not msg.isdigit():
        send_message("You must inform the task id", chat)
    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return
        for t in task.dependencies.split(',')[:-1]:
            qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
            t = qy.one()
            t.parents = t.parents.replace('{},'.format(task.id), '')
        db.session.delete(task)
        db.session.commit()
        send_message("Task [[{}]] deleted".format(task_id), chat)

def moveTask(msg, chat, status):
    if not msg.isdigit():
        send_message("You must inform the task id", chat)
    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return
        task.status = status
        db.session.commit()
        return task


def setPriorityInATask(msg, chat):
    text = ''
    if msg != '':
        if len(msg.split(' ', 1)) > 1:
            text = msg.split(' ', 1)[1]
        msg = msg.split(' ', 1)[0]

    if not msg.isdigit():
        send_message("You must inform the task id", chat)
    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return

        if text == '':
            task.priority = ''
            send_message("_Cleared_ all priorities from task {}".format(task_id), chat)
        else:
            if text.lower() not in ['high', 'medium', 'low']:
                send_message("The priority *must be* one of the following: high, medium, low", chat)
            else:
                task.priority = text.lower()
                send_message("*Task {}* priority has priority *{}*".format(task_id, text.lower()), chat)
        db.session.commit()

def setDependent(msg, chat):
    text = ''
    if msg != '':
        if len(msg.split(' ', 1)) > 1:
            text = msg.split(' ', 1)[1]
        msg = msg.split(' ', 1)[0]

    if not msg.isdigit():
        send_message("You must inform the task id", chat)
    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return

        if text == '':
            for i in task.dependencies.split(',')[:-1]:
                i = int(i)
                q = db.session.query(Task).filter_by(id=i, chat=chat)
                t = q.one()
                t.parents = t.parents.replace('{},'.format(task.id), '')

            task.dependencies = ''
            send_message("Dependencies removed from task {}".format(task_id), chat)
        else:
            for depid in text.split(' '):
                if not depid.isdigit():
                    send_message("All dependencies ids must be numeric, and not {}".format(depid), chat)
                else:
                    depid = int(depid)
                    query = db.session.query(Task).filter_by(id=depid, chat=chat)
                    try:
                        taskdep = query.one()
                        taskdep.parents += str(task.id) + ','
                    except sqlalchemy.orm.exc.NoResultFound:
                        send_message("_404_ Task {} not found x.x".format(depid), chat)
                        continue

                    deplist = task.dependencies.split(',')
                    if str(depid) not in deplist:
                        task.dependencies += str(depid) + ','

        db.session.commit()
        send_message("Task {} dependencies up to date".format(task_id), chat)


def handle_updates(updates):
    for update in updates["result"]:
        if 'message' in update:
            message = update['message']
        elif 'edited_message' in update:
            message = update['edited_message']
        else:
            print('Can\'t process! {}'.format(update))
            return

        command = message["text"].split(" ", 1)[0]
        msg = ''
        if len(message["text"].split(" ", 1)) > 1:
            msg = message["text"].split(" ", 1)[1].strip()

        chat = message["chat"]["id"]

        print(command, msg, chat)

        if command == '/new':
            creteNewTask(chat, msg)
        elif command == '/rename':
            renameTask(msg, chat)
        elif command == '/duplicate':
            createDuplicate(msg, chat)
        elif command == '/delete':
            deleteTask(msg, chat)
        elif command == '/todo':
            task = moveTask(msg, chat, 'TODO')
            if(task):
                send_message("*TODO* task [[{}]] {}".format(task.id, task.name), chat)
        elif command == '/doing':
            task = moveTask(msg, chat, 'DOING')
            if(task):
                send_message("*DOING* task [[{}]] {}".format(task.id, task.name), chat)
        elif command == '/done':
            task = moveTask(msg, chat, 'DONE')
            if (task):
                send_message("*DONE* task [[{}]] {}".format(task.id, task.name), chat)
        elif command == '/list':
            list(chat)
        elif command == '/dependson':
            setDependent(msg, chat)
        elif command == '/setPriority':
            setPriorityInATask(msg, chat)
        elif command == '/showPriority':
            showPriority(chat)
        elif command == '/start':
            send_message("Welcome! Here is a list of things you can do.", chat)
            send_message(HELP, chat)
        elif command == '/help':
            send_message("Here is a list of things you can do.", chat)
            send_message(HELP, chat)
        else:
            send_message("I'm sorry dave. I'm afraid I can't do that.", chat)


def main():
    last_update_id = None

    while True:
        print("Updates")
        updates = get_updates(last_update_id)

        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)

        time.sleep(0.5)


if __name__ == '__main__':
    main()
