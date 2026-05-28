需要扫描的内容：

- 后端Python（FastAPI）：`week6/backend/`
- 前端JavaScript：`week6/frontend/`
- 依赖关系：`week6/requirements.txt`
- Config/env（用于秘密）：文件中的`week6/`



📊 扫描概览

| 项目     | 数值                             |
| -------- | -------------------------------- |
| 扫描文件 | 19 个                            |
| 运行规则 | 486 条                           |
| 发现问题 | **5 个（全部是 Blocking 级别）** |

① CORS 通配符 — `backend/app/main.py` 第 24 行

```python
allow_origins=["*"]
```

**风险：** `*` 代表允许任何网站访问你的 API，当其余网站跨域调用当前API时，会集齐容易收集信息，造成风险。

解决方案：把`*`改成指定的域名即可。



② SQL 注入 — `backend/app/routers/notes.py` 第 71-79 行

```python
sql = text(f"SELECT ... WHERE title LIKE '%{q}%' ...")
```

风险： 用户输入的 `q` 直接拼进 SQL，攻击者可以输入 `' OR 1=1 --` 窃取所有数据。这是最严重的漏洞之一。

解决方案： 用参数绑定替代字符串拼接，彻底杜绝 SQL 注入风险。



③ `eval()` 代码注入 — `backend/app/routers/notes.py` 第 104 行

```python
result = str(eval(expr))
```

**风险：** `eval()` 会执行传入的任意字符串当 Python 代码。如果用户能控制 `expr`，就能在你的服务器上执行任意命令。

④ Shell 注入 — `backend/app/routers/notes.py` 第 112 行

```python
subprocess.run(cmd, shell=True, ...)
```

**风险：** `shell=True` 让命令经过 shell 解析，攻击者可能注入额外的系统命令。

⑤ 动态 URL 文件读取 — `backend/app/routers/notes.py` 第 120 行

```python
with urlopen(url) as res:
```

**风险：** `urllib` 支持 `file://` 协议，如果用户控制了 URL，可能读取服务器上的任意文件（如 `/etc/passwd`）。

这几个地方问题一致，基本都是处于端口便于测试时给了一些命令相关的权限，但是权限过高容易被攻击