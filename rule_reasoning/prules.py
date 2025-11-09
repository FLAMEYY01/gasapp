#=================================================================================#
# 基于规则的符号知识建模与推理系统                                                   #
#---------------------------------------------------------------------------------#
# 规则模型的数据结构：                                                              #
# (1) 用嵌套list表示                                                               #
# (2) rules[[规则CF值，结论，前提1，前提2，前提3]，[规则CF，结论，前提1，前提2]，...]  #
# (3) 规则数量任意，且每条规则的前提数量动态可变                                      #  
# 函数调用结构：                                                                   #
#=================================================================================#
import streamlit as st
import pandas as pd
import os
import signal
import time
# import sys
# ==================== 全局参数 ====================
app_port = os.environ.get("APP_PORT", "未知端口")
app_text = os.environ.get("APP_TEXT", "源文件管控App")
# *********************************************************************************
# 全局变量定义：用于widgets-UI控件的唯一key设置
global mywidgets_key_n
mywidgets_key_n = 0
# ---------------------------------------------------------------------------------
#
def Setup_a_Unique_Widget_Key():
  global mywidgets_key_n
  mywidgets_key = 'w' + chr(mywidgets_key_n)
  mywidgets_key_n = mywidgets_key_n + 1
  return mywidgets_key
#-----------------------------------------------------------------------------#
# 函数04：在本程序内 设置通用推理结束标志事实                                     #
#-----------------------------------------------------------------------------#
def Setup_a_Reasoning_Goal(reasoning_goal):
  reasoning_goal=[]
  reasoning_goal=['<推理目标 has-been 达成>'] # Set up an ending condition of rule-based forward reasoning
  return reasoning_goal
#-----------------------------------------------------------#
# 函数06：显示规则集及其静态事实集                             #
#-----------------------------------------------------------#
def Show_Rules(rules): 
  rule_n = len(rules)
  premises = [[] for i in range(rule_n)] 
  conclusion = ['' for i in range(rule_n)]
  cf_value = ['' for i in range(rule_n)]
  for i in range(rule_n):
    for j in range(2, len(rules[i])):
      premises[i].append(str(rules[i][j])) # take premises （仍是嵌套LIST）from rules LIST
    conclusion[i] = 'THEN: ' + str(rules[i][1])   # take conclusion from rules LIST
    cf_value[i] = str(rules[i][0])     # take cf_value grom rules LIST 
  #
  # 显示规则集的规则部分：
  st.write('规则集: ')
  # 生成组合后的前提list，共rule_n个前提字符串str  
  premises_combined = ['' for i in range(rule_n)]
  for i in range(rule_n):
    j = 0
    premise_temp = str()  
    for j in range(len(premises[i])): 
      if j==0:
        premise_temp = 'IF: ' + str(premises[i][j]) 
        continue  
      else: 
        premise_temp = premise_temp + ' .&. ' + str(premises[i][j]) 
    premises_combined[i] = premise_temp
  # 定义一个用于显示pandas的DataFrame对象的规则集字典rules_d
  rule_d = {'前提': premises_combined, '结论': conclusion, 'CF值': cf_value}
  rules_table = pd.DataFrame(data=rule_d)
  st.write(rules_table)
  return
#------------------------------------------------------------------------------
#
def Show_Static_Facts(staticfacts): 
  # 显示规则集的静态事实部分：
  st.write('静态事实集: ')
  staticfacts_n = len(staticfacts)
  staticfacts_d = {'静态事实': staticfacts, 'CF值': ['1.0' for i in range(staticfacts_n)]}
  staticfacts_table = pd.DataFrame(data=staticfacts_d)
  st.write(staticfacts_table)
  return
#-----------------------------------------------------------#
# 函数07：输入用于推理的初始用户事实                           #
#-----------------------------------------------------------#
def Input_Initial_User_Facts(initialfacts_prompt_space, initial_user_facts):
  mywidgets_key = Setup_a_Unique_Widget_Key()
  initial_user_facts=st.multiselect('从以下多选框中选择用于规则推理的初始用户事实:  ... ', initialfacts_prompt_space, key=mywidgets_key)
  # st.write('初选的规则推理初始事实 = ', initial_user_facts)
  mywidgets_key = Setup_a_Unique_Widget_Key()  
  my_button = st.button('ok', key=mywidgets_key)
  # After inputting, the program can be executed. 
  if my_button == True:
    st.write('已选定的用户初始事实: ')
    st.write(initial_user_facts)
    # st.write('----------------------------------------------')
    return initial_user_facts
  else:
    return []
#--------------------------------------------------------------#
# 函数08：初始化用于推理的动态事实栈表                            #
#--------------------------------------------------------------#
def Initialize_Dynamic_Stack(initial_user_facts, staticfacts, dynamic_stack):
   # set intial values in the dynamic stack
   dynamic_stack=[]
   dynamic_stack = initial_user_facts + staticfacts # The sequence is very important!
   return dynamic_stack 
#-------------------------------------------------------------#
# 函数9：获取1个或多个被成功匹配的规则子集                      #
#-------------------------------------------------------------#
def Get_a_Matched_Rule_Subset(rule_n, rules, dynamic_stack, triggered_rule_no_subset, current_matched_rule_no_subset):
  # 把规则集中的每条规则，分离成前提序列、结论和CF值
  premises=[[] for i in range(rule_n)] 
  conclusion=[]
  cf_value=[]
  for i in range(rule_n):
    for j in range(2, len(rules[i])):      # take premises （仍是嵌套LIST）from rules LIST
      premises[i].append(str(rules[i][j]))
    conclusion.append(str(rules[i][1]))    # take conclusion from rules LIST
    cf_value.append(str(rules[i][0]))      # take cf_value grom rules LIST 
  #
  # 寻找除掉已经被激活的规则子集后的成功匹配的规则子集LIST "current_matched_rule_no_subset" 
  current_matched_rule_no_subset = []
  for i in range(rule_n):
    # 检查当前规则是否已经以被激活成功？如果已经激活，则不再匹配！
    testing_rule_no = str()  # 其必须是字符串，才能放到LIST-triggered_rule_no_subset中，去查找有没有test_rule_no存在?
    testing_rule_no = str(i)
    if testing_rule_no in triggered_rule_no_subset:
      continue
    current_matched_times=0
    for j in range(len(dynamic_stack)-1, -1, -1):
      if dynamic_stack[j] in premises[i]:  # 检测动态事实栈表中的第j个事实是否与第i个规则中的某个前提匹配？
        current_matched_times = current_matched_times + 1
      else:
        continue
    if current_matched_times == len(premises[i]): # 判断当前与动态事实栈表中事实匹配成功的数量是不是等于当前规则的前提数？
      current_matched_rule_no_subset.append(str(i)) # 把匹配的规则放到相应的LIST中
  return current_matched_rule_no_subset
#----------------------------------------------------------------------------#
# 函数10：获取当前的1条被激活规则                                              #
#    多规则匹配成功后的冲突消解策略：确保只有1条规则被激活！                      #
#    冲突消解策略：                                                           #
#    1 -- 第一个被匹配的规则优先激活！                                         #
#    2 -- 前提最多的规则被激活，当前提数相等时，第一个被匹配的规则被激活！         # 
#    3 -- 重要度高的规则被激活！                                               #
#----------------------------------------------------------------------------#
def Trigger_a_Rule_after_Solving_Conflicits(current_matched_rule_no_subset, triggering_strategy, rule_n, rules, current_triggered_rule_no):
  # 未找到匹配的规则，推理失败!
  if len(current_matched_rule_no_subset) == 0: 
    st.write('📢 :red[TIPS: 当前的规则推理失败，系统退出！]')
    exit()
  # 只匹配成功一个规则：
  if len(current_matched_rule_no_subset) == 1:
    current_triggered_rule_no.append(current_matched_rule_no_subset[0])
    return current_triggered_rule_no
  # 匹配成功的规则多于1个：
  # triggering_strategy=1：第一个被匹配的规则优先激活！
  # triggering_strategy=2：前提最多的规则被激活，当前提数相等时，第一个被匹配的规则被激活！
  # triggering_strategy=3：重要度高的规则被激活！
  # case 2和3的情况未编程处理!!!
  if len(current_matched_rule_no_subset) > 1:
    # 第一个被匹配的规则优先激活！
    if triggering_strategy == 1:
      current_triggered_rule_no.append(current_matched_rule_no_subset[0])
      return current_triggered_rule_no
    # 前提最多的规则被激活，当前提数相等时，第一个被匹配的规则被激活！
    if triggering_strategy == 2:
      # 此处使用rules进行处理
      return current_triggered_rule_no
    # 重要度高的规则被激活！
    if triggering_strategy == 3:
      # 此处使用rules进行处理        
      return current_triggered_rule_no
#--------------------------------------------------------------#
# 函数11：更新用于推理的动态事实栈表                              #
#--------------------------------------------------------------#
def Update_Dynamic_Stack(current_triggered_rule_no, rules, dynamic_stack):
  successful_conclusion=[]
  temp_rule_no = str()
  temp_rule_no = str(current_triggered_rule_no[0]) # LIST必须先转成str，然后再转成int。不能直接转！
  i = int()
  i = int(temp_rule_no)
  successful_conclusion.append(str(rules[i][1]))
  dynamic_stack.append(str(successful_conclusion[0]))
  return dynamic_stack
#----------------------------------------------------------#
# 函数12：显示推理结果                                       #
#----------------------------------------------------------#  
def Output_Reasoning_Results(dynamic_stack, triggered_rule_no_subset, rules):
  # 选择输出推理结果方式：
  #
  output_mode = 0
  # 显示推理结果1：列出最后一个推理而得到的结论
  if output_mode == 0:
    one_conclusion = str()
    one_conclusion = str(dynamic_stack[len(dynamic_stack)-2])
    st.write('⚙️ :rainbow[本次推理的结果是: ]', one_conclusion) 
    # 显示推理路径：列出推理而出的所有结论 
    st.write('✒️ :rainbow[推理路径：激活的规则子集: ]')
    for i in range(len(triggered_rule_no_subset)):
      st.write('第', i+1, '个激活成功的规则号：', str(triggered_rule_no_subset[i]))
      triggered_rule = [[] for i in range(1)]
      triggered_rule[0] = rules[int(triggered_rule_no_subset[i])]
      Show_Rules(triggered_rule)
  return
#
# 函数：取excel文件中的一列中的所有数据 ----------------------------------------
#
def Get_a_Column_to_List_from_a_DF(df, column_name, a_column_list):
  a_column_list = df[column_name].tolist()
  # 使用列表推导式删除 '<>' 元素
  a_new_column_list = [element for element in a_column_list if element != "<>"]        
  a_column_list = a_new_column_list
  return a_column_list
#
# 函数：把从excel文件读进来的规则及分解成规则、静态事实和用户初始事实提示空间 -----
#
def Decompose_into_Rules_StaticFacts_UserFacts(df):
  # 从df中取出'Rule'列：
  temp_rules = []
  temp_rules = Get_a_Column_to_List_from_a_DF(df, 'Rule', temp_rules)
  # 生成程序中的rule嵌套表：
  rule_n = len(temp_rules)
  # 串分割，生成规则List
  rules = [[] for i in range(rule_n)]
  for i in range(rule_n):
    rules[i] = temp_rules[i].split(', ') # temp_rules[i]是字符串，用", "隔开。注意，在逗号后有空格      
  #
  # 得到静态事实集：    
  staticfacts = []
  staticfacts = Get_a_Column_to_List_from_a_DF(df, 'Static_Fact', staticfacts)
  #
  # 得到用户可输入的事实提示空间：
  initialfacts_prompt_space = []
  initialfacts_prompt_space = Get_a_Column_to_List_from_a_DF(df, 'Potential_Input_Fact', initialfacts_prompt_space)
  #
  return rules, staticfacts, initialfacts_prompt_space
#
# 函数：从本地或服务器端选择规则集的excel文件 ----------------------------------
#
def Select_a_Ruleset_from_Directories(df):
  # 选择从本地或从服务器端下载规则集excel文件：
  my_directory = -1
  while my_directory == -1:
    my_directory = {0: ":material/add: 从本地文件目录加载规则集Ruleset",
                    1: ":material/add: 从服务器端文件目录加载规则集Ruleset"}
    mywidgets_key = Setup_a_Unique_Widget_Key()
    my_selection = st.pills("🎑 选择规则集加载来源: ", 
                            options=my_directory.keys(),
                            format_func=lambda option: my_directory[option],
                            selection_mode="single", 
                            key=mywidgets_key)
    #
    # 从本地加载规则集的excel文件：
    #
    if my_selection == 0:
      # 创建文件上传器
      mywidgets_key = Setup_a_Unique_Widget_Key()
      uploaded_file = st.file_uploader('选择上传一个Excel文件: ', type=['xlsx', 'xls'], key=mywidgets_key)
      if uploaded_file is not None:
        # 读取 Excel 文件到 DataFrame
        df = pd.read_excel(uploaded_file)
        # st.write("本地规则集文件内容如下：")
        # st.dataframe(df)
        return(df)
    #
    # 从服务器端加载规则集excel文件：   
    #
    if my_selection == 1: 
      # 假设子目录名为 'excel_files'，你可以按需修改
      excel_files = []
      sub_dir = '.\\rulesets\\'  # 也可写成'./rulesets/', 或者'rulesets'、'./rulesets'
      if os.path.exists(sub_dir):
        for root, dirs, files in os.walk(sub_dir):
          for file in files:
            if file.endswith(('.xlsx', '.xls')):
              excel_files.append(os.path.join(root, file))
      if excel_files:
        mywidgets_key = Setup_a_Unique_Widget_Key()
        selected_file = st.selectbox("选择上传一个Excel文件: ", excel_files, key=mywidgets_key)
        mywidgets_key = Setup_a_Unique_Widget_Key()
        if st.button("加载文件", key=mywidgets_key):
          df = pd.read_excel(selected_file)
          # st.write("文件内容如下：")
          # st.dataframe(df)
          return(df)
        else:
          st.warning("在子目录中未找到Excel文件。")
      else:
        st.error("指定的子目录不存在。") 
#-----------------------------------------------------------------------
#
def Help_for_Using_Webapp_Integrator(page_n): 
    doc_images_path = './rule_reasoning/images/'+ 'page'
    for i in range(page_n):
        doc_image = doc_images_path + str(i+1) + '.png'
        st.image(doc_image)
    return  
#=======================================================================
# 主程序： Main Program
#=======================================================================
def main():
  st.set_page_config(layout='wide')  # 设置UI界面适配web浏览器的宽度
  container_heigth = 560 # 设置container的高度
  st.image('./rule_reasoning/images/title.jpg')  # 设置webapp标题
  # 设置运行与显示tab区域
  tab1, tab2, tab3, tab4 = st.tabs(['📚 选择规则集', 
                                    '🔭 正向推理求解ing ...', 
                                    '🗒️ 用户手册', 
                                    '👣 退出系统'])
  # tab1区域：选择规则集
  with tab1:
    with st.container(border=True, height=container_heigth):
      #
      # 步骤1：导入规则集、静态事实集、表达推理目标结束标志的静态事实 
      # 将 df 赋值为空的DataFrame
      df = pd.DataFrame()
      df = Select_a_Ruleset_from_Directories(df)
      if df is not None:
        rules, staticfacts, initialfacts_prompt_space = Decompose_into_Rules_StaticFacts_UserFacts(df)
        #
        # for i in range(len(rules)):
        #   st.write('rules[', i, ']=', rules[i])    
        # st.write('static_facts =', staticfacts)    
        # st.write('prompt_space =', initialfacts_prompt_space)     
        #
        reasoning_goal=[]
        reasoning_goal = Setup_a_Reasoning_Goal(reasoning_goal)
        # 步骤2：显示规则集和静态事实
        Show_Rules(rules) # 显示规则集
        Show_Static_Facts(staticfacts) # 显示静态事实
    # 
    # Tab2区域：推理求解...
  with tab2:
    with st.container(border=True, height=container_heigth):      
    # 步骤3：从与规则集相关的所有初始用户输入事实构成的提示空间中，选择当前推理的初始用户输入事实    
      if df is not None: 
        initial_user_facts=[]
        # st.write('prompt_space =', initialfacts_prompt_space)             
        initial_user_facts = Input_Initial_User_Facts(initialfacts_prompt_space, initial_user_facts)
        if initial_user_facts != []:
          # 步骤4：设置初始的动态事实栈表
          dynamic_stack=[]
          dynamic_stack = Initialize_Dynamic_Stack(initial_user_facts, staticfacts, dynamic_stack)
          #
          # 步骤5：执行基于规则的正向推理
          triggered_rule_no_subset=[]
          while dynamic_stack[len(dynamic_stack)-1] != reasoning_goal[0]:  # 检查是否达到推理目标？
            # 选择出所有和动态事实栈表中事实完全匹配的规则
            current_matched_rule_no_subset=[]
            rule_n = len(rules)
            current_matched_rule_no_subset = Get_a_Matched_Rule_Subset(rule_n, rules, dynamic_stack, triggered_rule_no_subset, current_matched_rule_no_subset)
            # 利用冲突消解准则，选择出一个激活的规则
            current_triggered_rule_no=[]
            triggering_strategy=1
            current_triggered_rule_no = Trigger_a_Rule_after_Solving_Conflicits(current_matched_rule_no_subset, triggering_strategy, rule_n, rules, current_triggered_rule_no)
            # 更新动态事实栈表
            dynamic_stack = Update_Dynamic_Stack(current_triggered_rule_no, rules, dynamic_stack)
            # 记录当前被激活的规则号，生成被激活规则路径
            triggered_rule_no_subset.append(str(current_triggered_rule_no[0]))
            # 结束“while循环”！
          else:  
            st.write(':red[TIPS: 推理结束，将显示推理结果！]')
          #
          # 步骤6：输出推理结果
          Output_Reasoning_Results(dynamic_stack, triggered_rule_no_subset, rules)
  #
  with tab3:
    with st.container(border=True, height=container_heigth):
      page_n = 5
      Help_for_Using_Webapp_Integrator(page_n)
  # 
  with tab4:
    with st.container(border=True, height=container_heigth):    
      st.write('休息一下，再选择radio控件的按钮，继续运行本系统！')
      # 暂停系统：
      st.write('提示：暂停系统的运行，但不退出浏览器！如想完全退出系统，请点击关闭浏览器的图标')
      st.code("🚪 退出子应用")
      st.warning("⚠️ 确认后将终止该 Streamlit 应用进程。")

  return
#========================= 主程序函数结束 ！ ==========================================#
if __name__ == '__main__':
  main()
#========================= End ！ ====================================================#