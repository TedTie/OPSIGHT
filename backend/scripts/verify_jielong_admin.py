#!/usr/bin/env python3
"""
快速验证：管理员在“全部”范围下能看到 assignment_type=all 的接龙任务所有记录

- 登录 admin / jlpss-chenjianxiong / test_user
- 向一个接龙(all)任务分别提交两条记录
- 以管理员视角（全部）与“我的”对比返回总数
"""

import requests
import sys

BASE = 'http://localhost:8000/api/v1'

def login(session: requests.Session, username: str) -> bool:
    r = session.post(f'{BASE}/auth/login', json={'username': username}, timeout=10)
    print(f'login {username}:', r.status_code)
    if r.status_code != 200:
        print(r.text)
    return r.status_code == 200

def main():
    sess_admin = requests.Session()
    sess_mgr = requests.Session()
    sess_user = requests.Session()

    # 登录
    if not login(sess_admin, 'admin'):
        print('admin 登录失败'); sys.exit(1)
    if not login(sess_mgr, 'jlpss-chenjianxiong'):
        print('管理员登录失败'); sys.exit(1)
    if not login(sess_user, 'test_user'):
        print('test_user 登录失败'); sys.exit(1)

    # 找到一个接龙(all)任务
    r = sess_admin.get(f'{BASE}/tasks', params={'size': 100}, timeout=10)
    print('tasks list:', r.status_code)
    if r.status_code != 200:
        print(r.text); sys.exit(1)
    body = r.json()
    tasks = body.get('items') or body
    jid = None
    for t in tasks:
        if t.get('task_type') == 'jielong' and t.get('assignment_type') == 'all':
            jid = t['id']; break
    print('selected jielong task id:', jid)
    if not jid:
        print('未找到接龙(all)任务，请先创建'); sys.exit(0)

    # 分别提交记录
    payloads = [
        {'id': 'A001', 'remark': 'admin-记录', 'intention': 'yes'},
        {'id': 'U001', 'remark': 'user-记录', 'intention': 'maybe'},
    ]
    pr1 = sess_admin.post(f'{BASE}/tasks/{jid}/jielong', json=payloads[0], timeout=10)
    print('admin post:', pr1.status_code, pr1.text[:120])
    pr2 = sess_user.post(f'{BASE}/tasks/{jid}/jielong', json=payloads[1], timeout=10)
    print('user post:', pr2.status_code, pr2.text[:120])

    # 管理员视角：全部
    gr_all = sess_mgr.get(f'{BASE}/tasks/{jid}/jielong', timeout=10)
    print('manager GET all:', gr_all.status_code)
    try:
        print('items total(all):', gr_all.json().get('total'))
    except Exception as e:
        print('解析失败(all):', e, gr_all.text[:160])

    # 管理员视角：我的
    # 管理员 id 假定为2（jlpss-chenjianxiong），若不同可由 /auth/me 获取
    me = sess_mgr.get(f'{BASE}/auth/me', timeout=10)
    mgr_id = me.json().get('id') if me.status_code == 200 else 2
    gr_mine = sess_mgr.get(f'{BASE}/tasks/{jid}/jielong', params={'user_id': mgr_id}, timeout=10)
    print('manager GET mine:', gr_mine.status_code)
    try:
        print('items total(mine):', gr_mine.json().get('total'))
    except Exception as e:
        print('解析失败(mine):', e, gr_mine.text[:160])

if __name__ == '__main__':
    main()