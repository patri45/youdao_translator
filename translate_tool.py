from bs4 import BeautifulSoup
import requests
import threading

"""
Version: 0.1 alpha
Last edited time: 2/2/2021
Author: Xin Jin
Email: jinxin4545@gmail.com
"""

# 基本完成，多线程翻译
# 特点，自动排版，自动分析语言，
# 不足，1 因为有道自身问题，有些句子无法翻译，排查过网站，并非爬虫的原因 2 即使用了多线程，但效率一般，可能还不如单线程
# 解决方法 可以引入其他翻译作为补充，或者可以考虑随机生成header重新搜索，不知是否有效

class YDtranslate:
    def __init__(self):
        self._URL_ = "http://youdao.com/w/eng/{}"
        self.original_lines_list=[]
        self.youdao_result_dict={}
        self.web_result_dict={}

    def run(self,lines_str):
        # 线程池
        thread_list = []

        # 清洗原文本
        lines=lines_str.split("\n")
        counter=0
        for line in lines:
            if line=="" or line==" ":
                pass
            else:
                self.original_lines_list.append(line.strip())
                self.youdao_result_dict[counter] = []
                self.web_result_dict[counter] = []
                new_thread = threading.Thread(target=self._translate, args=(counter,))  # 为每行文本添加单独线程，搜索
                thread_list.append(new_thread)
                thread_list[counter].start()  # 启动线程并阻塞
                thread_list[counter].join()
                counter+=1

        return self._return_reformat_result()

    def get_comparative_translation(self):
        # 返回双语对照翻译
        result=[]
        for index in range(len(self.original_lines_list)):
            result.append(self.original_lines_list[index])
            trans_line=self.youdao_result_dict[index]
            if trans_line==[] and len(self.web_result_dict[index])>=1:
                trans_line=self.web_result_dict[index]

            if len(trans_line)>=1:
                result.append(trans_line[0])
            else:
                result.append("")
        return result

    def get_youdao_web_translation(self):
        # 返回有道翻译和网络翻译
        result=["origin:","youdao:","web:"]
        for index in range(len(self.original_lines_list)):
            result[0] = result[0] + " " + self.original_lines_list[index]
            result[1]=result[1]+" "+",".join(self.youdao_result_dict[index])
            result[2] = result[2] + " " + ",".join(self.web_result_dict[index])
        return result

    def _translate(self,index):
        # 获取网页文本
        line=self.original_lines_list[index]
        url = self._URL_.format(line)

        # 设定重复搜索次数，反有道反爬 => 该功能似乎无效，可在引入其他翻译后，移除
        repeated_time=0
        while repeated_time<=3:
            html_content = self._get_content(url)
            soup = BeautifulSoup(html_content, "lxml")
            if self._isEnglish(line):
                result = self._e2zh(soup)
            else:
                result = self._zh2e(soup)
            if result["youdao"]!=[]:
                break
            repeated_time+=1
        self.youdao_result_dict[index]=result["youdao"]
        self.web_result_dict[index]=result["web"]

    def _get_content(self,url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'}
        return requests.get(url, headers=headers).text

    def _zh2e(self,soup):
        # 无有道翻译，有机器翻译
        youdao_trans_list = []
        target = soup.find(lambda tag: tag.name == "p" and '以上为机器翻译' in tag.text)
        if target != None:
            children = target.parent.findChildren("p")
            if children != None:
                youdao_trans_list.append(children[1].text)

        # 有道翻译
        if youdao_trans_list==[]:
            youdao_container = soup.find(name='p',attrs={"class":"wordGroup"})
            #print(youdao_container)
            if youdao_container!=None:
                children = youdao_container.findChildren("a" )
                #print(youdao_container)
                if children != None:
                    for child in children:
                        youdao_trans_list.append(child.text)
            #print(youdao_trans_list)

        # 网络翻译
        web_trans_list = []
        web_container = soup.find(name='div',attrs={"id":"webTransToggle"})
        if web_container!= None:
            children = web_container.findChildren("span" )
            if children != None:
                for child in children:
                    if child.has_attr('class'):
                        pass
                    else:
                        web_trans_list.append(child.text.strip())
        #print(web_trans_list)

        return {"youdao": youdao_trans_list,"web":web_trans_list}

    def _e2zh(self,soup):
        # 无有道翻译，有机器翻译
        youdao_trans_list = []
        target = soup.find(lambda tag: tag.name == "p" and '以上为机器翻译' in tag.text)
        if target != None:
            children = target.parent.findChildren("p")
            if children != None:
                youdao_trans_list.append(children[1].text)

        # 有道翻译
        if youdao_trans_list == []:
            youdao_container = soup.find(name='div',attrs={"class":"trans-container"})
            if youdao_container!=None:
                children = youdao_container.findChildren("li" )
                #print(youdao_container)
                if children != None:
                    for child in children:
                        youdao_trans_list.append(child.text)
                #print(youdao_trans_list)

        # 网络翻译
        web_trans_list = []
        web_container = soup.find(name='div',attrs={"id":"webTransToggle"})
        if web_container!=None:
            children = web_container.findChildren("span" )
            if children != None:
                for child in children:
                    if child.has_attr('class'):
                        pass
                    else:
                        web_trans_list.append(child.text.strip())
        #print(web_trans_list)

        return {"youdao": youdao_trans_list,"web":web_trans_list}

    def _isEnglish(self,s):
        letters = "qQwWeErRtTyYuUiIoOpPaAsSdDfFgGhHjJkKlLzZxXcCvVbBnNmM"
        punctuation = r"!@#$%^&*()[]{}|/\-`_+<>?:.,; "
        result = False
        all_counts = 0
        e_letters_counts = 0
        for l in s:
            if l in punctuation:
                pass
            elif l in letters:
                e_letters_counts += 1
                all_counts += 1
            else:
                all_counts += 1
        # print(all_counts)
        # print(e_letters_counts)
        e_ratio = round(e_letters_counts / all_counts, 2)
        # print(e_ratio)
        if e_ratio >= 0.8:
            result = True
        # print(result)
        return result

    def _return_reformat_result(self):
        if len(self.original_lines_list)>1:
            return self.get_comparative_translation()
        else:
            return self.get_youdao_web_translation()

yd=YDtranslate()
word='''
我最近在做一个程序(你可以从我之前问的问题中看到)，我在理解和实现多线程方面遇到了真正的困难。
'''
result=yd.run(word)
for line in result:
    print(line)