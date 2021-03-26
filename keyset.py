from automateDJL import utils

s = input("service: ")
u = input("user: ")
p = input("pwd: ")
util = utils.Utils("battery.conf")
util.setKey(s, u, p)

pwd = util.getKey(s, u)
print(f"pwd {pwd}")
