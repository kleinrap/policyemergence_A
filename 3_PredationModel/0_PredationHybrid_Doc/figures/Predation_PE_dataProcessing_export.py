import pandas as pd
import matplotlib.pyplot as plt
import ast
import itertools

'''
This is a file used to convert the dense model file into a palatable file for the agents of the policy emergence model. The new file is filled with pandas

Example line:
0,0,"[None, None]",
"[	[0, 'policymaker', 0, None, None, None, [[0, 0.0, 0], [0, 0.95, 0.396], [0, 0.5, 0.208], [0, 0.95, 0.396], [0, 0.95, 0.376], [0, 0.5, 0.346], [0, 0.95, 0.278], [0], [0], [0], [0.95], [0.9], [-0.5], [-0.8], [0.95], [0.2], [0.9], [0.7], [1.0]]],
	[1, 'policymaker', 0, None, None, None, [[0, 0.0, 0], [0, 0.95, 0.396], [0, 0.5, 0.208], [0, 0.95, 0.396], [0, 0.95, 0.376], [0, 0.5, 0.346], [0, 0.95, 0.278], [0], [0], [0], [0.95], [0.9], [-0.5], [-0.8], [0.95], [0.2], [0.9], [0.7], [1.0]]],
	[2, 'policyentrepreneur', 0, None, None, None, [[0, 0.0, 0], [0, 0.95, 0.396], [0, 0.5, 0.208], [0, 0.95, 0.396], [0, 0.95, 0.376], [0, 0.5, 0.346], [0, 0.95, 0.278], [0], [0], [0], [0.95], [0.9], [-0.5], [-0.8], [0.95], [0.2], [0.9], [0.7], [1.0]]],
	[3, 'policyentrepreneur', 0, None, None, None, [[0, 0.0, 0], [0, 0.95, 0.396], [0, 0.5, 0.208], [0, 0.95, 0.396], [0, 0.95, 0.376], [0, 0.5, 0.346], [0, 0.95, 0.278], [0], [0], [0], [0.95], [0.9], [-0.5], [-0.8], [0.95], [0.2], [0.9], [0.7], [1.0]]],
	[4, 'policymaker', 1, None, None, None, [[0, 0.0, 0], [0, 0.75, 0.441], [0, 0.0, 0.0], [0, 0.95, 0.559], [0, 0.95, 0.437], [0, 0.0, 0.233], [0, 0.95, 0.33], [0], [0], [0], [0.95], [0.9], [-0.5], [-0.8], [0.95], [0.2], [0.9], [0.7], [1.0]]],
	[5, 'policyentrepreneur', 1, None, None, None, [[0, 0.0, 0], [0, 0.75, 0.441], [0, 0.0, 0.0], [0, 0.95, 0.559], [0, 0.95, 0.437], [0, 0.0, 0.233], [0, 0.95, 0.33], [0], [0], [0], [0.95], [0.9], [-0.5], [-0.8], [0.95], [0.2], [0.9], [0.7], [1.0]]],
	[6, 'policyentrepreneur', 1, None, None, None, [[0, 0.0, 0], [0, 0.75, 0.441], [0, 0.0, 0.0], [0, 0.95, 0.559], [0, 0.95, 0.437], [0, 0.0, 0.233], [0, 0.95, 0.33], [0], [0], [0], [0.95], [0.9], [-0.5], [-0.8], [0.95], [0.2], [0.9], [0.7], [1.0]]]]"
	,"[[0, 25, [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]], [1, 75, [0.0, 0.5, 0.2, 0.75, 0.75, 0.4, 1.0]]]"

'''
# global parameters
total_runs = 50  # number of simulations
total_steps_PM = 16
PE_type = 'A+Co'
scenario = 7

# FOCUSING ON THE RESULTS OF THE POLICY EMERGENCE MODEL
# initiliasation of lists
PM_model = []

# the different columns of the panda
# ['Unnamed: 0', 'step', 'AS_PF', 'agent_attributes']

print(scenario, PE_type)

for i in range(total_runs):
	if i >= 0:  # for checks
		print('File ', i, ' being exported.')
		PM_model = pd.read_csv('O_PE_model_Sce' + str(scenario) + '_Run' + str(i) + '_type' + str(PE_type) +'.csv')

		PM_model = PM_model.drop(0)  # dropping the first line of the pandas

		steps_PM = []
		AS_PF = []
		agent_attributes = []
		electorate_attributes = []


		# saving the paremeters in different arrays
		for index, row in PM_model.iterrows():
			steps_PM.append(index)
			AS_PF.append(row['AS_PF'])
			agent_attributes.append(row['agent_attributes'])
			electorate_attributes.append(row['electorate_attributes'])	
			# print(row['electorate_attributes'])

		# eval(agent_attributes[step])[agent number][agent attribute]
		# number in array:
		# 0 _unique_id
		# 1 agent_type
		# 2 affiliation
		# 3 selected_PC
		# 4 selected_PF
		# 5 selected_S
		# 6 selected_PI
		# 7 issuetree[_unique_id]
		# 8 policytree[_unique_id]

		steps = []
		unique_id_s = []
		agent_type_s = []
		affiliation_s = []
		selected_PC_s = []
		# selected_PF_s = []
		selected_S_s = []
		selected_PI_s = []
		issuetree_s = []
		# policytree_s = []

		# unpacking each attribute into a big list of list
		for j in range(total_steps_PM):
			for k in range(len(eval(agent_attributes[j]))):
				steps.append(j)
				unique_id_s.append(eval(agent_attributes[j])[k][0])
				agent_type_s.append(eval(agent_attributes[j])[k][1])
				affiliation_s.append(eval(agent_attributes[j])[k][2])
				selected_PC_s.append(eval(agent_attributes[j])[k][3])
				# selected_PF_s.append(eval(agent_attributes[j])[k][4])
				selected_S_s.append(eval(agent_attributes[j])[k][4])
				selected_PI_s.append(eval(agent_attributes[j])[k][5])
				issuetree_s.append(eval(agent_attributes[j])[k][6])
				# policytree_s.append(eval(agent_attributes[j])[k][7])

		steps_model = []
		AS_PC_s = []
		# AS_PF_s = []
		PIm_s = []

		# unpacking each attribute into a big list of list
		for j in range(total_steps_PM):
			steps_model.append(j)
			AS_PC_s.append(eval(AS_PF[j])[0])
			# AS_PF_s.append(eval(AS_PF[j])[1])
			PIm_s.append(eval(AS_PF[j])[1])


		steps_elec = []
		affiliation_elec_s = []
		representativeness_s = []
		issuetree_elec_s = []

		for j in range(total_steps_PM):
			for k in range(len(eval(electorate_attributes[j]))):

				steps_elec.append(j)
				affiliation_elec_s.append(eval(electorate_attributes[j])[k][0])
				representativeness_s.append(eval(electorate_attributes[j])[k][1])
				issuetree_elec_s.append(eval(electorate_attributes[j])[k][2])

		'''
		the aim of the operations performed below is to split the issue tree and policy tree into its components for ease of use later on 
		'''

		# creating the issuetree list
		issuetree_s_RA = []
		for j in range(len(list(itertools.chain.from_iterable(issuetree_s[0])))):
			issuetree_s_RA.append([])

		# policytree_s_RA = []
		# for j in range(len(list(itertools.chain.from_iterable(policytree_s[0])))):
		# 	policytree_s_RA.append([])

		# creating the issuetree list
		issuetree_elec_s_RA = []
		for j in range(len(issuetree_elec_s[0])):
			issuetree_elec_s_RA.append([])

		# splitting the issuetree_s
		for j in range(len(issuetree_s)):  # going through the ticks and through each agent
			merged_issue = list(itertools.chain.from_iterable(issuetree_s[j]))  # merging the entire tree into one big list
			# merged_policy = list(itertools.chain.from_iterable(policytree_s[j]))  # merging the entire tree into one big list

			for k in range(len(list(itertools.chain.from_iterable(issuetree_s[j])))): 
				issuetree_s_RA[k].append(merged_issue[k])  # assigning each parameter to a list in the list

			# for k in range(len(list(itertools.chain.from_iterable(policytree_s[0])))):
			# 	policytree_s_RA[k].append(merged_policy[k])  # assigning each parameter to a list in the list



		# splitting the issuetree_elec_s
		for j in range(len(issuetree_elec_s)):  # going through the ticks and through each agent

			merged_issue = issuetree_elec_s[j]  # merging the entire tree into one big list
			for k in range(len(issuetree_elec_s[j])): 
				issuetree_elec_s_RA[k].append(merged_issue[k])  # assigning each parameter to a list in the list

		# creating the rows for the panda composed of only individual cells and no lists 
		newpanda = {'steps': steps, 'ID': unique_id_s, 'type': agent_type_s, 'aff': affiliation_s, 'PC': selected_PC_s, 'S': selected_S_s, 'PI': selected_PI_s,
			'DCBe' : issuetree_s_RA[0], 'DCGo' : issuetree_s_RA[1], 'DCPref' : issuetree_s_RA[2],
			'PC1Be': issuetree_s_RA[3], 'PC1Go': issuetree_s_RA[4], 'PC1Pref': issuetree_s_RA[5],
			'PC2Be': issuetree_s_RA[6], 'PC2Go': issuetree_s_RA[7], 'PC2Pref': issuetree_s_RA[8],
			'PC3Be': issuetree_s_RA[9], 'PC3Go':issuetree_s_RA[10], 'PC3Pref':issuetree_s_RA[11],
			'S1Be' :issuetree_s_RA[12], 'S1Go' :issuetree_s_RA[13], 'S1Pref' :issuetree_s_RA[14],
			'S2Be' :issuetree_s_RA[15], 'S2Go' :issuetree_s_RA[16], 'S2Pref' :issuetree_s_RA[17],
			'S3Be' :issuetree_s_RA[18], 'S3Go' :issuetree_s_RA[19], 'S3Pref' :issuetree_s_RA[20],
			'PC1-DC': issuetree_s_RA[21],
			'PC2-DC': issuetree_s_RA[22],
			'PC3-DC': issuetree_s_RA[23],
			'PC1-S1': issuetree_s_RA[24],
			'PC1-S2': issuetree_s_RA[25],
			'PC1-S3': issuetree_s_RA[26],
			'PC2-S1': issuetree_s_RA[27],
			'PC2-S2': issuetree_s_RA[28],
			'PC2-S3': issuetree_s_RA[29],
			'PC3-S1': issuetree_s_RA[30],
			'PC3-S2': issuetree_s_RA[31],
			'PC3-S3': issuetree_s_RA[32]}

		df_newpanda = pd.DataFrame(data=newpanda)

		df_newpanda.to_csv('O_PE_agentsT_Sce' + str(scenario) + '_Run' + str(i) + '_type' + str(PE_type) + '.csv')

		# creating the rows for the panda composed of only individual cells and no lists 
		newpanda2 = {'steps': steps_model, 'AS_PC': AS_PC_s, 'PIm': PIm_s}

		df_newpanda2 = pd.DataFrame(data=newpanda2)

		df_newpanda2.to_csv('O_PE_modelT_Sce' + str(scenario) + '_Run' + str(i) + '_type' + str(PE_type) + '.csv')

		# creating the rows for the panda composed of only individual cells and no lists 
		newpanda3 = {'steps': steps_elec, 'electorate': affiliation_elec_s, 'representativeness': representativeness_s, 
			'DC': issuetree_elec_s_RA[0], 'PC1': issuetree_elec_s_RA[1], 'PC2': issuetree_elec_s_RA[2],
			'PC3': issuetree_elec_s_RA[3], 'S1': issuetree_elec_s_RA[4], 'S2': issuetree_elec_s_RA[5], 'S3': issuetree_elec_s_RA[6]}

		df_newpanda3 = pd.DataFrame(data=newpanda3)

		df_newpanda3.to_csv('O_PE_electoratesT_Sce' + str(scenario) + '_Run' + str(i) + '_type' + str(PE_type) + '.csv')

