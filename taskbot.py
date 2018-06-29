#!/usr/bin/env python3

import json
import requests
import time
import urllib

import sqlalchemy

import db
from db import Task

TOKEN = open("token.txt", 'r')
USER = open("user.txt", 'r').read()
PASSWORD = open("password.txt", 'r').read()
URL = "https://api.telegram.org/bot{}/".format(TOKEN.read())

HELP = """
 /new TITLE BODY
 /todo ID
 /doing ID
 /done ID
 /delete ID
 /list
 /rename ID TITLE
 /dependson ID ID...
 /duplicate ID
 /setPriority ID PRIORITY{low, medium, high}
 /showPriority
 /createIssue TITLE BODY
 /setDuedate ID DATE{DD/MM/YYYY}
 /help
"""
REPO_OWNER = 'TecProg-20181'
REPO_NAME = 'T--Tecbot'

def getUrl(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def getJsonFromUrl(url):
    content = getUrl(url)
    js = json.loads(content)
    return js


def getUpdates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = getJsonFromUrl(url)
    return js


def sendMessage(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    getUrl(url)


def getLastUpdateId(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))

    return max(update_ids)


def depsText(task, chat, preceed=''):
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
            line += depsText(dep, chat, preceed + '    ')
        else:
            line += '├── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
            line += depsText(dep, chat, preceed + '│   ')

        text += line

    return text

def printTasks(query, chat, message):
    for task in query.all():
        icon = '\U0001F195'
        if task.status == 'DOING':
            icon = '\U000023FA'
        elif task.status == 'DONE':
            icon = '\U00002611'
        if task.duedate == None:
            message += '[[{}]] {} {} _{}_\n'.format(task.id, icon, task.name, task.priority)
        else:
            message += '[[{}]] {} {} _{}_ {}\n'.format(task.id, icon, task.name, task.priority, task.duedate)
        message += depsText(task, chat)
    return message

def list(chat):
    query = db.session.query(Task).filter_by(parents='', chat=chat).order_by(Task.id)
    queryTODO = db.session.query(Task).filter_by(status='TODO', chat=chat).order_by(Task.id)
    queryDOING = db.session.query(Task).filter_by(status='DOING', chat=chat).order_by(Task.id)
    queryDONE = db.session.query(Task).filter_by(status='DONE', chat=chat).order_by(Task.id)

    text = ''
    text += '\U0001F4CB Task List\n'
    text = printTasks(query, chat, text)
    sendMessage(text, chat)
    text = ''
    text += '\U0001F4DD _Status_\n'
    text += '\n\U0001F195 *TODO*\n'
    text = printTasks(queryTODO, chat, text)
    text += '\n\U000023FA *DOING*\n'
    text = printTasks(queryDOING, chat, text)
    text += '\n\U00002611 *DONE*\n'
    text = printTasks(queryDONE, chat, text)
    sendMessage(text, chat)


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

    text = ''
    text += '\U0001F4CB Task List\n'
    text = printTasks(queryHigh, chat, text)
    text = printTasks(queryMedium, chat, text)
    text = printTasks(queryLow, chat, text)
    text = printTasks(query, chat, text)
    sendMessage(text, chat)

    text = ''
    text += '\U0001F4DD _Status_\n'
    text += '\n\U0001F195 *TODO*\n'
    text = printTasks(queryHighTODO, chat, text)
    text = printTasks(queryMediumTODO, chat, text)
    text = printTasks(queryLowTODO, chat, text)
    text = printTasks(queryTODO, chat, text)
    text += '\n\U000023FA *DOING*\n'
    text = printTasks(queryHighDOING, chat, text)
    text = printTasks(queryMediumDOING, chat, text)
    text = printTasks(queryLowDOING, chat, text)
    text = printTasks(queryDOING, chat, text)
    text += '\n\U00002611 *DONE*\n'
    text = printTasks(queryHighDONE, chat, text)
    text = printTasks(queryMediumDONE, chat, text)
    text = printTasks(queryLowDONE, chat, text)
    text = printTasks(queryDONE, chat, text)
    sendMessage(text, chat)


def creteNewTask(chat, msg):
    body = ''
    if msg != '':
        if len(msg.split(' ', 1)) > 1:
            body = msg.split(' ', 1)[1]
        title = msg.split(' ', 1)[0]

    task = Task(chat=chat, name=title, status='TODO', dependencies='', parents='', priority='')
    db.session.add(task)
    db.session.commit()
    sendMessage("New task *TODO* [[{}]] {}".format(task.id, task.name), chat)

def renameTask(msg, chat):
    text = ''
    if msg != '':
        if len(msg.split(' ', 1)) > 1:
            text = msg.split(' ', 1)[1]
        msg = msg.split(' ', 1)[0]

    if not msg.isdigit():
        sendMessage("You must inform the task id", chat)
    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            sendMessage("_404_ Task {} not found x.x".format(task_id), chat)
            return

        if text == '':
            sendMessage("You want to modify task {}, but you didn't provide any new text".format(task_id),
                         chat)
            return

        old_text = task.name
        task.name = text
        db.session.commit()
        sendMessage("Task {} redefined from {} to {}".format(task_id, old_text, text), chat)

def createDuplicate(msg, chat):
    if not msg.isdigit():
        sendMessage("You must inform the task id", chat)
    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            sendMessage("_404_ Task {} not found x.x".format(task_id), chat)
            return

        dtask = Task(chat=task.chat, name=task.name, status=task.status, dependencies=task.dependencies,
                     parents=task.parents, priority=task.priority, duedate=task.duedate)
        db.session.add(dtask)

        for t in task.dependencies.split(',')[:-1]:
            qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
            t = qy.one()
            t.parents += '{},'.format(dtask.id)

        db.session.commit()
        sendMessage("New task *TODO* [[{}]] {}".format(dtask.id, dtask.name), chat)

def deleteTask(msg, chat):
    if not msg.isdigit():
        sendMessage("You must inform the task id", chat)
    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            sendMessage("_404_ Task {} not found x.x".format(task_id), chat)
            return
        for t in task.dependencies.split(',')[:-1]:
            qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
            t = qy.one()
            t.parents = t.parents.replace('{},'.format(task.id), '')
        db.session.delete(task)
        db.session.commit()
        sendMessage("Task [[{}]] deleted".format(task_id), chat)

def moveTask(msg, chat, status):
    text = ''
    for _id in msg.split(' '):
        if not _id.isdigit():
            sendMessage("You must inform the task id", chat)
        else:
            task_id = int(_id)
            query = db.session.query(Task).filter_by(id=task_id, chat=chat)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                sendMessage("_404_ Task {} not found x.x".format(task_id), chat)
                return
            task.status = status
            db.session.commit()
            text += status
            text += " task [[{}]] {}\n".format(task.id, task.name)
    return text


def setPriorityInATask(msg, chat):
    text = ''
    if msg != '':
        if len(msg.split(' ', 1)) > 1:
            text = msg.split(' ', 1)[1]
        msg = msg.split(' ', 1)[0]

    if not msg.isdigit():
        sendMessage("You must inform the task id", chat)
    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            sendMessage("_404_ Task {} not found x.x".format(task_id), chat)
            return

        if text == '':
            task.priority = ''
            sendMessage("_Cleared_ all priorities from task {}".format(task_id), chat)
        else:
            if text.lower() not in ['high', 'medium', 'low']:
                sendMessage("The priority *must be* one of the following: high, medium, low", chat)
            else:
                task.priority = text.lower()
                sendMessage("*Task {}* priority has priority *{}*".format(task_id, text.lower()), chat)
        db.session.commit()

def setDependent(msg, chat):
    text = ''
    if msg != '':
        if len(msg.split(' ', 1)) > 1:
            text = msg.split(' ', 1)[1]
        msg = msg.split(' ', 1)[0]

    if not msg.isdigit():
        sendMessage("You must inform the task id", chat)
    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            sendMessage("_404_ Task {} not found x.x".format(task_id), chat)
            return

        if text == '':
            for i in task.dependencies.split(',')[:-1]:
                i = int(i)
                q = db.session.query(Task).filter_by(id=i, chat=chat)
                t = q.one()
                t.parents = t.parents.replace('{},'.format(task.id), '')

            task.dependencies = ''
            sendMessage("Dependencies removed from task {}".format(task_id), chat)
        else:
            for depid in text.split(' '):
                if not depid.isdigit():
                    sendMessage("All dependencies ids must be numeric, and not {}".format(depid), chat)
                else:
                    depid = int(depid)
                    query = db.session.query(Task).filter_by(id=depid, chat=chat)
                    try:
                        taskdep = query.one()
                        taskdep.parents += str(task.id) + ','
                    except sqlalchemy.orm.exc.NoResultFound:
                        sendMessage("_404_ Task {} not found x.x".format(depid), chat)
                        continue

                    deplist = task.dependencies.split(',')
                    if str(depid) not in deplist:
                        task.dependencies += str(depid) + ','

        db.session.commit()
        sendMessage("Task {} dependencies up to date".format(task_id), chat)

def createGithubIssue(msg, chat):

    body = ''
    if msg != '':
        if len(msg.split(' ', 1)) > 1:
            body = msg.split(' ', 1)[1]
        title = msg.split(' ', 1)[0]

    url = 'https://api.github.com/repos/%s/%s/issues' % (REPO_OWNER, REPO_NAME)

    session = requests.session()
    session.auth = (USER, PASSWORD)

    issue = {'title': title, "body": body}

    r = session.post(url, json.dumps(issue))

    if r.status_code == 201:
        sendMessage('Successfully created Issue', chat)
    else:
        sendMessage('Could''t create Issue', chat)


def setDueDate(chat, msg):
    """Set date to the task."""
    text = ''
    task = Task

    if msg != '':
        if len(msg.split(' ', 1)) > 1:
            text = msg.split(' ', 1)[1]
        msg = msg.split(' ', 1)[0]

    if not msg.isdigit():
        sendMessage("You have to inform the task id", chat)

    else:
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)

        try:
            task = query.one()

        except sqlalchemy.orm.exc.NoResultFound:
            sendMessage("_404_ Task {} not found x.x".format(task_id), chat)

    if text == '':
        task.duedate = ''
        sendMessage("_Cleared_ due date from task {}".format(task_id), chat)

    else:
        text = text.split("/")
        text.reverse()
    if not (1 <= int(text[2]) <= 31 and 1 <= int(text[1]) <= 12 and 2018 <= int(text[0])):
        sendMessage(
        "The date format is: *DD/MM/YYYY* Max day = 31, Max mouth = 12 and Min year = 2018)", chat)

    else:
        from datetime import datetime
        task.duedate = datetime.strptime(" ".join(text), '%Y %m %d')
        sendMessage(
         "Task {} has the due date *{}*".format(task_id, task.duedate), chat)
        db.session.commit()


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
            createGithubIssue(msg, chat)        
            creteNewTask(chat, msg)
        elif command == '/createIssue':
            createGithubIssue(msg, chat)        
        elif command == '/duedate':
            setDueDate(chat, msg)
        elif command == '/rename':
            renameTask(msg, chat)
        elif command == '/duplicate':
            createDuplicate(msg, chat)
        elif command == '/delete':
            deleteTask(msg, chat)
        elif command == '/todo':
            task = moveTask(msg, chat, 'TODO')
            if(task):
                sendMessage(task, chat)
                list(chat)
        elif command == '/doing':
            task = moveTask(msg, chat, 'DOING')
            if(task):
                sendMessage(task, chat)
                list(chat)
        elif command == '/done':
            task = moveTask(msg, chat, 'DONE')
            if(task):
                sendMessage(task, chat)
                list(chat)
        elif command == '/list':
            list(chat)
        elif command == '/dependson':
            setDependent(msg, chat)
        elif command == '/setPriority':
            setPriorityInATask(msg, chat)
        elif command == '/showPriority':
            showPriority(chat)
        elif command == '/start':
            sendMessage("Welcome! Here is text list of things you can do.", chat)
            sendMessage(HELP, chat)
        elif command == '/help':
            sendMessage("Here is text list of things you can do.", chat)
            sendMessage(HELP, chat)
        else:
            sendMessage("I'm sorry dave. I'm afraid I can't do that.", chat)

def main():
    last_update_id = None

    while True:
        print("Updates")
        updates = getUpdates(last_update_id)

        if len(updates["result"]) > 0:
            last_update_id = getLastUpdateId(updates) + 1
            handle_updates(updates)

        time.sleep(0.5)


if __name__ == '__main__':
    main()
