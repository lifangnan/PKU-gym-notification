# -*- coding: utf-8
from browser import Browser
import json, time
# from datetime import datetime
import datetime
import pyautogui
import pyperclip


class PKUVenue():
	def __init__(self, config):
		self.username = config["username"]
		self.password = config["password"]
		self.phone = config["phone"]
		self.orderStatement = []
		self.browser = Browser()


	def send(self, msg):
		# 复制需要发送的内容到粘贴板
		pyperclip.copy(msg)
		# 模拟键盘 ctrl + v 粘贴内容
		pyautogui.hotkey('ctrl', 'v')
		# 发送消息
		pyautogui.press('enter')

	def send_msg(self, friend = "文件传输助手", msg = ""):
		# Ctrl + alt + w 打开微信
		pyautogui.hotkey('ctrl', 'alt', 'w')
		# 搜索好友
		pyautogui.hotkey('ctrl', 'f')
		# 复制好友昵称到粘贴板
		pyperclip.copy(friend)
		# 模拟键盘 ctrl + v 粘贴
		pyautogui.hotkey('ctrl', 'v')
		time.sleep(0.5)
		# 回车进入好友消息界面
		pyautogui.press('enter')
		# 一条一条发送消息
		self.send(msg)
		# 每条消息间隔 2 秒
		# time.sleep(2)

		# Ctrl + alt + w 关闭微信
		pyautogui.hotkey('ctrl', 'alt', 'w')


	def login(self):
		self.browser.gotoPage("https://epe.pku.edu.cn/ggtypt/login?service=https://epe.pku.edu.cn/venue-server/loginto")
		print("trying to login ......")
		self.browser.typeByCssSelector("#user_name", self.username)
		self.browser.typeByCssSelector("#password", self.password)
		self.browser.clickByCssSelector("#logon_button")
		self.browser.findElementByCssSelector("body > div.fullHeight > div > div > div.isLogin > div > div.loginUser")
		print("login success !!!!")

	def _reqListToDict(self, reqList):
		reqDict = {}
		for req in reqList:
			orderDate = req.split(" ")[0]
			orderTime = req.split(" ")[1]
			if orderDate in reqDict.keys():
				reqDict[orderDate].append(orderTime)
			else:
				reqDict[orderDate] = [orderTime]
		return reqDict

	def __jumpToDate(self, orderDate):
		print("selecting date %s" % orderDate)
		today = datetime.datetime.now()
		orderDatetime = datetime.datetime.strptime(orderDate, "%Y-%m-%d")
		dayDelta = (orderDatetime - today).days + 1
		for i in range(0, dayDelta):
			self.browser.clickByXPath("/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/form/div/div/button[2]/i")
		# waiting for the table to show up
		self.browser.findElementByXPath("/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/div[3]/div[1]/div/div/div/div/div/table/tbody/tr[15]/td[1]/div")

	def __submitOrder(self):
		print("read & agree ✅!!!!")
		self.browser.clickByXPath("/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/div[4]/label/span/input")

		print("click to make order......")
		self.browser.clickByXPath("/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/div[5]/div/div[2]")

		print("submiting order ....... ")
		self.browser.typeByXPath("/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/form/div/div[4]/div/div/div/div/input", self.phone)
		# self.browser.clickByXPath("/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/div/div/div[2]")

	def __makeOrder(self, sportsName, timeList, courtPriorityList, courtIndexDict, orderDate, orderTimeList, gym_name="邱德拔"):
		orderEnable = False
		currentPageIndex = 0
		pageJumpButtonIndex = [None, 6, 2]
		for ot in orderTimeList:
			print("selecting time %s ........." % ot)
			timeTableRow = timeList.index(ot)+1
			courtSelected = False
			for court in courtPriorityList:
				courtPageIndex = courtIndexDict[court]["page"]
				courtTableColumn = courtIndexDict[court]["column"]
				# judge whether jump page or not
				pageDelta = courtPageIndex - currentPageIndex
				jumpDirection = 1 if pageDelta > 0 else -1
				for _ in range(0, pageDelta, jumpDirection):
					# print("current url:", self.browser.browser.current_url)
					self.browser.clickByXPath("/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/div[3]/div[1]/div/div/div/div/div/table/thead/tr/td[%d]/div/span/i" % pageJumpButtonIndex[jumpDirection])
					currentPageIndex += jumpDirection

				# select court block
				courtBlockElment = self.browser.findElementByXPath("/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/div[3]/div[1]/div/div/div/div/div/table/tbody/tr[%d]/td[%d]/div" % (timeTableRow, courtTableColumn+1))
				if "free" in courtBlockElment.get_attribute('class'):
					courtBlockElment.click()
					courtSelected = True
					self.orderStatement.append("%s %s %s %s" % (sportsName, orderDate, ot, court))
					# print("selected %s %s %s" % (orderDate, ot, court))
					for friend_name in friends_list:
						self.send_msg(friend= friend_name, msg = "【自动消息】\n%s %s %s %s,该时段有空闲场" % (orderDate, ot, court, gym_name))
					print("有空闲场：%s %s %s" % (orderDate, ot, court))
					break
			if not courtSelected:
				self.orderStatement.append("%s %s %s %s" % (sportsName, orderDate, ot, "无场"))
				# print("without court left at %s %s" % (orderDate, ot))
				# self.send_msg(msg = "【自动消息】\n%s %s %s,该时段没有空闲场" % (orderDate, ot, gym_name))
				# print("该时段没有空闲场 %s %s" % (orderDate, ot))
			else:
				orderEnable = True

		return orderEnable

	def _order(self, sportsName, venueUrl, timeList, courtPriorityList, courtIndexDict, orderDate, orderTimeList):
		self.browser.gotoPage(venueUrl)
		self.__jumpToDate(orderDate)
		if(venueUrl == "https://epe.pku.edu.cn/venue/pku/venue-reservation/60"):
			if self.__makeOrder(sportsName, timeList, courtPriorityList, courtIndexDict, orderDate, orderTimeList, gym_name="邱德拔"):
				# print(orderDate, orderTimeList, '有空闲场')
				# self.__submitOrder()
				pass
		elif(venueUrl == "https://epe.pku.edu.cn/venue/pku/venue-reservation/86"):
			if self.__makeOrder(sportsName, timeList, courtPriorityList, courtIndexDict, orderDate, orderTimeList, gym_name="五四体育馆"):
				# print(orderDate, orderTimeList, '有空闲场')
				# self.__submitOrder()
				pass

	def orderBadmintonOnce(self, orderDate, orderTimeList):
		timeList = ["8:00-9:00","9:00-10:00","10:00-11:00","11:00-12:00","12:00-13:00","13:00-14:00","14:00-15:00","15:00-16:00","16:00-17:00","17:00-18:00","18:00-19:00","19:00-20:00","20:00-21:00","21:00-22:00"]
		# courtList = [["1号", "2号", "3号", "4号", "5号"], ["6号", "7号", "8号", "9号", "10号"], ["11号", "12号"]]
		# 原程序顺序
		# courtPriorityList = ["3号", "4号", "9号", "10号", "1号", "2号", "5号", "6号", "7号", "8号", "11号", "12号"]
		courtPriorityList = ['12号', '11号', '8号', '7号', '6号', '5号', '2号', '1号', '10号', '9号', '4号', '3号']
		courtIndexDict = {
			"1号" : {"page": 0, "column": 1},
			"2号" : {"page": 0, "column": 2},
			"3号" : {"page": 0, "column": 3},
			"4号" : {"page": 0, "column": 4},
			"5号" : {"page": 0, "column": 5},
			"6号" : {"page": 1, "column": 1},
			"7号" : {"page": 1, "column": 2},
			"8号" : {"page": 1, "column": 3},
			"9号" : {"page": 1, "column": 4},
			"10号": {"page": 1, "column": 5},
			"11号": {"page": 2, "column": 1},
			"12号": {"page": 2, "column": 2}
		}
		self._order("羽毛球", "https://epe.pku.edu.cn/venue/pku/venue-reservation/60", timeList, courtPriorityList, courtIndexDict, orderDate, orderTimeList)


	def orderBadmintonOnce_54(self, orderDate, orderTimeList):
		timeList = ["8:00-9:00","9:00-10:00","10:00-11:00","11:00-12:00","12:00-13:00","13:00-14:00","14:00-15:00","15:00-16:00","16:00-17:00","17:00-18:00","18:00-19:00","19:00-20:00","20:00-21:00","21:00-22:00"]
		# courtList = [["1号", "2号", "3号", "4号", "5号"], ["6号", "7号", "8号", "9号", "10号"], ["11号", "12号"]]
		# 原程序顺序
		# courtPriorityList = ["3号", "4号", "9号", "10号", "1号", "2号", "5号", "6号", "7号", "8号", "11号", "12号"]
		courtPriorityList = ['9号', '8号', '7号', '6号', '5号', '4号', '3号', '2号', '1号']
		courtIndexDict = {
			"1号" : {"page": 0, "column": 1},
			"2号" : {"page": 0, "column": 2},
			"3号" : {"page": 0, "column": 3},
			"4号" : {"page": 0, "column": 4},
			"5号" : {"page": 0, "column": 5},
			"6号" : {"page": 1, "column": 1},
			"7号" : {"page": 1, "column": 2},
			"8号" : {"page": 1, "column": 3},
			"9号" : {"page": 1, "column": 4},
		}
		self._order("羽毛球", "https://epe.pku.edu.cn/venue/pku/venue-reservation/86", timeList, courtPriorityList, courtIndexDict, orderDate, orderTimeList)


	def orderBadminton(self, reqList):
		reqDict = self._reqListToDict(reqList)

		# 当前可以订的场的日期
		now = datetime.datetime.now()
		if(now.time() < datetime.time(hour=12)):
			before_date = now.date()+datetime.timedelta(days=2)
		else:
			before_date = now.date()+datetime.timedelta(days=3)

		for orderDate in reqDict:
			# 不在可预定的时间，则跳过
			if( datetime.datetime.strptime(orderDate, "%Y-%m-%d").date() > before_date):
				continue
			for i in range(0, len(reqDict[orderDate]), 2):
				self.orderBadmintonOnce(orderDate, reqDict[orderDate][i:i+2])
				self.orderBadmintonOnce_54(orderDate, reqDict[orderDate][i:i+2])

	def orderBasketballOnce(self, orderDate, orderTimeList):
		timeList = ["8:00-9:00","9:00-10:00","10:00-11:00","11:00-12:00","12:00-13:00","13:00-14:00","14:00-15:00","15:00-16:00","16:00-17:00","17:00-18:00","18:00-19:00","19:00-20:00","20:00-21:00","21:00-22:00"]
		# courtList = [["北1", "南1", "北2", "南2"]]
		courtPriorityList = ["北1", "南1", "北2", "南2"]
		courtIndexDict = {
			"北1" : {"page": 0, "column": 1},
			"南1" : {"page": 0, "column": 2},
			"北2" : {"page": 0, "column": 3},
			"南2" : {"page": 0, "column": 4}
		}
		self._order("篮球", "https://epe.pku.edu.cn/venue/pku/venue-reservation/68", timeList, courtPriorityList, courtIndexDict, orderDate, orderTimeList)


	def orderBasketball(self, reqList):
		reqDict = self._reqListToDict(reqList)
		for orderDate in reqDict:
			for i in range(0, len(reqDict[orderDate]), 2):
				self.orderBasketballOnce(orderDate, reqDict[orderDate][i:i+2])

	def outputOrderStatement(self):
		for i in range(0, len(self.orderStatement)):
			print("{:^52}".format(" " + "-" * 50 + " "))
			print("| " + "{:^48}".format(self.orderStatement[i]) + " |")
			print("{:^52}".format(" " + "-" * 50 + " "))

	def __del__(self):
		self.browser.close()



# 将微信消息发送给下列好友!!!!!!!!!!!!!
friends_list = ["文件传输助手"]

def main():
	with open("./config.json", "r", encoding="utf8") as f:
		config = json.load(f)

	last_datetime = datetime.datetime(year=2000, month=1, day=1)

	while True:
		now_datetime = datetime.datetime.now()
		now_time = now_datetime.time()

		# 距离上次查询超过1小时，则重新登陆
		if(now_datetime - last_datetime > datetime.timedelta(minutes=30)):
			pkuvenue = PKUVenue(config["user_info"])
			pkuvenue.login()
			last_datetime = now_datetime

		# 起止时间
		start_time = datetime.time(hour=6, minute=0)
		end_time = datetime.time(hour=23, minute=59)
		if(now_time > start_time and now_time < end_time):
			for k in config["order"].keys():
				if k == u"羽毛球":
					pkuvenue.orderBadminton(config["order"][k])
		
		# 每间隔半小时查询依次
		time.sleep(1800)


	# # waiting until rushtime
	# now = datetime.datetime.now()
	# rushtime = datetime.datetime.strptime(config["rushtime"], "%Y-%m-%d %H:%M:%S")
	# if (rushtime - now).total_seconds() > 0:
	# 	time.sleep((rushtime - now).total_seconds())

	# for k in config["order"].keys():
	# 	if k == u"羽毛球":
	# 		pkuvenue.orderBadminton(config["order"][k])
	# 	elif k == u"篮球":
	# 		pkuvenue.orderBasketball(config["order"][k])

	# pkuvenue.outputOrderStatement()

	del pkuvenue

if __name__=="__main__":
	main()