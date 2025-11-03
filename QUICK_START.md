# OPSIGHT - Quick Start Guide 🚀

## ⚡ 30-Second Start

```bash
# 1. Start everything
python minimal_launcher.py

# 2. Open browser
# Go to: http://localhost:3000

# 3. Login with any username:
# admin, manager1, consultant1, teacher1, tutor1, assistant1
```

## 🎯 Choose Your Version

| Version | Command | When to Use |
|---------|---------|-------------|
| **Simplified** ⭐ | `python minimal_launcher.py` | **Recommended** - Full features, minimal deps |
| **Ultra-Minimal** | `cd backend/minimal && python start.py` | 3 dependencies only, basic features |
| **Full Docker** | `docker-compose up -d` | Production deployment |

## 🔑 Account Quick Reference

| Username | Role | What You Can Do |
|----------|------|-----------------|
| **admin** | 🔴 Super Admin | Everything |
| **manager1** | 🟡 Admin | Create tasks, view reports |
| **consultant1** | 🔵 User | Complete tasks, view own data |
| **teacher1** | 🔵 User | Complete tasks, view own data |
| **tutor1** | 🔵 User | Complete tasks, view own data |
| **assistant1** | 🔵 User | Complete tasks, view own data |

## 📍 Important URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🎯 Four Task Types

1. **💰 Amount** - Sales targets, money goals
2. **🔢 Quantity** - Count-based objectives
3. **🔗 Jielong** - Sequential data collection
4. **✅ Checkbox** - Simple completion tasks

## 🚀 Common Actions

### Create Task (Admin+)
```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -b "username=admin" \
  -d '{"title": "Sales Target", "task_type": "amount", "target_amount": 50000}'
```

### Complete Task (User)
```bash
curl -X POST "http://localhost:8000/api/v1/tasks/1/complete" \
  -b "username=consultant1" \
  -d '{"completion_value": 15000}'
```

### View My Tasks
```bash
curl "http://localhost:8000/api/v1/tasks?assigned_to_me=true" \
  -b "username=consultant1"
```

## 🆘 Troubleshooting

**Port already in use?**
```bash
# Kill existing processes
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

**Database corrupted?**
```bash
# Reset everything
rm backend/simple_app.db
python minimal_launcher.py
```

**Can't login?**
- Check browser console
- Verify backend is running: http://localhost:8000/health
- Try clearing cookies

## 📞 Need Help?

1. **Check API docs**: http://localhost:8000/docs
2. **Check system health**: http://localhost:8000/health
3. **Review logs**: Terminal output shows errors
4. **Test accounts**: Use different usernames to test permissions

---

**Happy Task Managing!** 🎉

*This system is designed for internal use - simple, effective, and easy to customize.*