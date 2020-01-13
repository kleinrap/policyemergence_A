# imports for the policy emergence model
from model_PE import PolicyEmergenceSM
from model_PE_policyImpact import policy_impact_evaluation
from model_PE_agents import ElectorateAgent

# imports for the policy context model
from model_predation import WolfSheepPredation

# import other packages
import pandas as pd

# policy emergence model selection
'''	
Model types
	SM: simplest model 				['SM']
	A: ACF
		+PL: Policy learning 		['A+PL']
		+Co: Coalition				['A+Co']
		+PK: Partial knowledge		['A+PK']
		+PI: Partial information	['A+PI']
'''
PE_type = 'A+PL'

# batch run parameters
repetitions_runs = 50
sce_number = 2

# running parameters
total_ticks = 1600
interval_tick = 100
run_tick = int(total_ticks/interval_tick)
warmup_tick = interval_tick

# parameters of the policy context model
'''
Here go all the parameters that are needed to initialise the policy context model
'''

# parameters of the policy emergence model
'''for all scenarios'''
res_aff = [0 for p in range(sce_number)]
# resources per affiliation agent out of 100
res_aff[0] = [75, 25] # for scenario 0
res_aff[1] = [25, 75] # for scenario 1

# electorate representativeness per affiliation
repr = [0 for p in range(sce_number)]
repr[0] = [25, 75] # for scenario 0
repr[1] = [25, 75] # for scenario 1

# list - [-] - electorate influence weight constant [per scenario]
w_el_inf = [0 for p in range(sce_number)]
w_el_inf[0] = 0 # for scenario 0
w_el_inf[1] = 0 # for scenario 1

'''actor distribution'''
PE_agents = [0 for p in range(sce_number)]
PE_PMs_0 = 3  # number of policy makers
PE_PEs_0 = 8  # number of policy entrepreneurs
PE_EPs_0 = 0  # number of external parties
PE_agents[0] = [PE_PMs_0, PE_PEs_0, PE_EPs_0] # for scenario 0
PE_agents[1] = [PE_PMs_0, PE_PEs_0, PE_EPs_0] # for scenario 1

PE_aff = [0 for p in range(sce_number)]
PE_PMs_aff_0 = [2, 1]  # policy maker distribution per affiliation
PE_PEs_aff_0 = [4, 4]  # policy entrepreneur distribution per affiliation
PE_EPs_aff_0 = [0, 0]  # external parties distribution per affiliation
PE_aff[0] = [PE_PMs_aff_0, PE_PEs_aff_0, PE_EPs_aff_0] # for scenario 0
PE_aff[1] = [PE_PMs_aff_0, PE_PEs_aff_0, PE_EPs_aff_0] # for scenario 1

# input profile for preferred states
'''
This can be used for different scenarios for the preferred states (goals) of the policy emergence agents
'''
input_goalProfiles_file_Ex0Be = 'input_goalProfiles_Ex0Be'
input_goalProfiles_file_Ex1Be = 'input_goalProfiles_Ex1Be'
goal_input_Ex0Be = pd.read_csv(input_goalProfiles_file_Ex0Be, sep=',')
goal_input_Ex1Be = pd.read_csv(input_goalProfiles_file_Ex1Be, sep=',')
goal_profiles_Ex0Be = []
goal_profiles_Ex1Be = []
for i in range(sce_number*2):
	goal_profiles_Ex0Be.append(goal_input_Ex0Be.iloc[i].tolist())  # goal profiles for active agents and electorate
	goal_profiles_Ex1Be.append(goal_input_Ex1Be.iloc[i].tolist())  # goal profiles for active agents and electorate

# first goal input profile (after change)
input_goalProfiles_file_Ex0Af = 'input_goalProfiles_Ex0Af'
goal_input_Ex0Af = pd.read_csv(input_goalProfiles_file_Ex0Af, sep=',')
goal_profiles_Ex0Af = []
for i in range(sce_number*2):
	goal_profiles_Ex0Af.append(goal_input_Ex0Af.iloc[i].tolist())  # goal profiles for active agents and electorate

# putting all of the profiles into two list for the different experiments (one for initial goals and one for the goals
# after the mid-change)
goal_prof = [goal_profiles_Ex0Be, goal_profiles_Ex1Be]
goal_prof_after = [goal_profiles_Ex0Af, goal_profiles_Ex0Af]


# running a number of scenarios
''' changes in the agent distribution '''
for sce_i in range (sce_number):

	# creating the agents for the policy emergence model
	# PE_inputs = [PE_PMs, PE_PMs_aff, PE_PEs, PE_PEs_aff, PE_EPs, PE_EPs_aff, res_aff, repr,
	# 			 goal_profiles[sce_i], w_el_inf[sce_i]]

	PE_inputs = [PE_agents[sce_i], PE_aff[sce_i], res_aff[sce_i], repr[sce_i], goal_prof[sce_i], w_el_inf[sce_i]]

	# running a number of repetitions per experiment
	for rep_runs in range(repetitions_runs):

		# for model run tailoring
		if sce_i >= 0:

			# initialisation of the policy context model
			model_run_predation = WolfSheepPredation(50, 50, 100, 50, 0.04, 0.05, 30, True, 30, 4)

			# initialisation of the policy emergence model
			model_run_PE = PolicyEmergenceSM(PE_type, PE_inputs, 10, 10)

			print("\n")
			print("************************")
			print("Start of the simulation:", "\n")
			for i in range(run_tick):

				print(" ")
				print("************************")
				print("Tick number: ", i, ', scenario:', sce_i, ', w_el', w_el_inf[sce_i], ', run number:', rep_runs)

				# warm up time
				# this is also used as a warmup time
				if i == 0:
					policy_chosen = [None for ite in range(len(model_run_PE.policy_instruments[0]))]
					for warmup_time in range(warmup_tick):
						KPIs = model_run_predation.step(policy_chosen)

				# policy impact evaluation
				policy_impact_evaluation(model_run_PE, model_run_predation, KPIs, interval_tick)

				# running the policy emergence model
				policy_chosen = model_run_PE.step(KPIs)

				# run of the policy context model for interval_tick ticks
				for p in range(interval_tick):
					KPIs = model_run_predation.step(policy_chosen)
					policy_chosen = [None for ite in range(len(model_run_PE.policy_instruments[0]))]
										# reset policy after it has been implemented once

				'''
				Scenario Changes
				In this part of the code, changes can be introduced through scenarios for both the policy context and
				the policy emergence models
				'''

				# # scenario 3 - electorate preferred state change
				# if i == 8 and sce_i == 3:
				# 	# changing the electorate preferred states values based on the scenarios input
				# 	aff_number = len(resources_aff)
				# 	for elec in model_run_PE.schedule.agent_buffer(shuffled=True):
				# 		if isinstance(elec, ElectorateAgent):
				# 			for issue in range(model_run_PE.len_DC + model_run_PE.len_PC + model_run_PE.len_S):
				# 				if elec.affiliation == 0:
				# 					elec.issuetree_elec[issue] = goal_prof_after[sce_i][aff_number + 0][1 + issue]
				# 				if elec.affiliation == 1:
				# 					elec.issuetree_elec[issue] = goal_prof_after[sce_i][aff_number + 1][1 + issue]

			# # checker code
				# for agent in model_run_PE.schedule.agent_buffer(shuffled=False):
				# 	if isinstance(agent, ActiveAgent):
				# 		print(' ')
				# 		print(agent.agent_type, '\n', 'ID', agent.unique_id, 'Aff', agent.affiliation,
			# 		agent.issuetree[agent.unique_id], '\n',
				# 		agent.policytree[agent.unique_id])


			# output of the data
			# policy context model
			output_policyContext_model = model_run_predation.datacollector.get_model_vars_dataframe()
			output_policyContext_model.to_csv('O_Pre_model_Sce' + str(sce_i) + '_Run' + str(rep_runs)
											  + '_el'  + str(w_el_influence[sce_i]) +'.csv')

			# policy emergence model
			output_PE_model = model_run_PE.datacollector.get_model_vars_dataframe()
			output_PE_model.to_csv('O_PE_model_Sce' + str(sce_i) + '_Run' + str(rep_runs)
								   + '_el' + str(w_el_influence[sce_i]) + '.csv')
			output_PE_agents = model_run_PE.datacollector.get_agent_vars_dataframe()
			output_PE_agents.to_csv('O_PE_agents_Sce' + str(sce_i) + '_Run' + str(rep_runs)
									+ '_el' + str(w_el_influence[sce_i]) + '.csv')