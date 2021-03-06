# imports for the policy emergence model
from model_PE import PolicyEmergenceSM
from model_PE_policyImpact import policy_impact_evaluation
from model_PE_agents import ActiveAgent, Coalition

# imports for the policy context model
from model_elec import Electricity

# import other packages
import pandas as pd
import random

def read_inputs_beliefs(res_aff, number, time):

	input_goalProfiles_file = 'input_goalProfiles_Ex' + str(number) + str(time)
	goal_input = pd.read_csv(input_goalProfiles_file, sep=',')
	goal_profiles = []
	for i in range(len(res_aff[0]) * 2):
		goal_profiles.append(goal_input.iloc[i].tolist())  # goal profiles for active agents and electorate

	return goal_profiles

# policy emergence model selection
'''	
Model types
	SM: simplest model 				['SM']
	A: ACF
		+PL: Policy learning 		['A+PL']
		+Co: Coalition				['A+Co']
		+PK: Partial knowledge		['+PK'] - Add-on
		+PI: Partial information	['+PI'] - Add-on
'''

# running parameters
total_ticks = 27
interval_tick = 3
run_tick = int(total_ticks/interval_tick)
warmup_tick = interval_tick
sce_number = 3 # total number of scenarios

# batch run parameters
repetitions_runs = 50

PE_type = [['A+Co'], ['A+Co'], ['A+Co']]

# ACF + PL parameters
con_lvl = [0.50, 0.75, 0.25]  # conflict levels [low, mid, high]
resources_spend_incr_agents = 0.10  # percentage of the resources spent by the agents for interactions
AplusPL_param = [con_lvl, resources_spend_incr_agents]

# ACF + Co parameters
PC_interest = [0 for p in range(sce_number)] # issue number around which coalitions assemble
coa_creation_thresh = 0.15  # threshold belief difference to create coalitions
coa_coherence_thresh = 0.10  # threshold belief difference to trigger coalition intra-actions
coa_resources_share = 0.50  # amount of resources assigned to coalitions from agents in coalitions
resources_spend_incr_coal = 0.05  # percentage of the resources spent by the coalition for interactions

# ACF + PK parameters
PK_catchup = 0.20
AplusPK_inputs = [PK_catchup]

# parameters of the policy context model
'''
Here go all the parameters that are needed to initialise the policy context model
'''

# parameters of the policy emergence model
'''for all scenarios'''

# resources per affiliation agent out of 100
res_aff = [[100, 75] for p in range(sce_number)]
res_aff[2] = [50, 100]  # changed for scenario 2

# electorate representativeness per affiliation
repr = [[25, 75] for p in range(sce_number)]

# list - [-] - electorate influence weight constant [per scenario]
w_el_inf = [0 for p in range(sce_number)]

'''actor distribution'''
PE_PMs_0 = 7  # number of policy makers
PE_PEs_0 = 23  # number of policy entrepreneurs
PE_EPs_0 = 0  # number of external parties
PE_agents = [[PE_PMs_0, PE_PEs_0, PE_EPs_0] for p in range(sce_number)]

PE_PMs_aff_0 = [4, 3]  # policy maker distribution per affiliation
PE_PEs_aff_0 = [15, 8]  # policy entrepreneur distribution per affiliation
PE_EPs_aff_0 = [0, 0]  # external parties distribution per affiliation
PE_aff = [[PE_PMs_aff_0, PE_PEs_aff_0, PE_EPs_aff_0] for p in range(sce_number)]

# input profile for preferred states
'''
This can be used for different scenarios for the preferred states (goals) of the policy emergence agents
'''

goal_prof = []
goal_prof_after = []
for i in range(sce_number):
	goal_prof.append(read_inputs_beliefs(res_aff, i, 'Be'))
	goal_prof_after.append(read_inputs_beliefs(res_aff, i, 'Af'))

# demand growth profile
demand_growth = [0.00, 0.015, 0.03]

print("\n")
# running a number of scenarios
''' changes in the agent distribution '''
for sce_i in range (sce_number):

	# going through the different demand scenarios
	for demand_ite in range(len(demand_growth)):

		PE_inputs = [PE_agents[sce_i], PE_aff[sce_i], res_aff[sce_i], repr[sce_i], goal_prof[sce_i], w_el_inf[sce_i]]

		# running a number of repetitions per experiment
		for rep_runs in range(repetitions_runs):

			# for model run tailoring
			if demand_ite == 2 and sce_i == 2 and rep_runs >= 25:

				print("PE_type:", PE_type[sce_i])
				print('sce.:', sce_i)
				print('growth:', demand_growth[demand_ite])
				print('run:', rep_runs)
				print('w_el', w_el_inf[sce_i])
				print('PC_interest:', PC_interest[sce_i])

				# initialisation of the policy context model
				model_run_elec = Electricity(demand_growth[demand_ite], 10, 10)

				AplusCo_inputs = [PC_interest[sce_i], coa_creation_thresh, coa_coherence_thresh, coa_resources_share,
								  resources_spend_incr_coal]

				# initialisation of the policy emergence model
				model_run_PE = PolicyEmergenceSM(PE_type[sce_i], PE_inputs, AplusPL_param, AplusCo_inputs, AplusPK_inputs, 10, 10)

				print("\n")
				print("************************")
				print("Start of the simulation:", "\n")
				for i in range(run_tick):

					print(" ")
					print("************************")
					print( "Tick: ", i)

					# warm up time
					# this is also used as a warmup time
					if i == 0:
						policy_chosen = [None for ite in range(len(model_run_PE.policy_instruments[0]))]
						for warmup_time in range(warmup_tick):
							KPIs = model_run_elec.step(policy_chosen)

					# policy impact evaluation
					policy_impact_evaluation(model_run_PE, model_run_elec, KPIs, interval_tick)

					# running the policy emergence model
					policy_chosen = model_run_PE.step(KPIs)

					# run of the policy context model for interval_tick ticks
					for p in range(interval_tick):
						KPIs = model_run_elec.step(policy_chosen)
						policy_chosen = [None for ite in range(len(model_run_PE.policy_instruments[0]))]
											# reset policy after it has been implemented once

					'''
					Scenario Changes
					In this part of the code, changes can be introduced through scenarios for both the policy context and
					the policy emergence models
					'''

					# scenario 1 - change in preferred states
					if i == 2 and sce_i == 1:
						print(' doing this ')
						# changing the electorate preferred states values based on the scenarios input
						for agent in model_run_PE.schedule.agent_buffer(shuffled=True):
							if isinstance(agent, ActiveAgent) and not isinstance(agent, Coalition):
								for issue in range(model_run_PE.len_DC + model_run_PE.len_PC + model_run_PE.len_S):
									if agent.affiliation == 0:
										agent.issuetree[agent.unique_id][issue][1] = \
											goal_prof_after[sce_i][agent.affiliation][1 + issue] \
											+ (2 * random.random() - 1) / 100
									if agent.affiliation == 1:
										agent.issuetree[agent.unique_id][issue][1] = \
											goal_prof_after[sce_i][agent.affiliation][1 + issue] \
											+ (2 * random.random() - 1) / 100

									if agent.issuetree[agent.unique_id][issue][1] > 1:
										agent.issuetree[agent.unique_id][issue][1] = 1
									if agent.issuetree[agent.unique_id][issue][1] < 0 or issue == 0:
										# DC are not considered here so kept at 0
										agent.issuetree[agent.unique_id][issue][1] = 0

				# # checker code
					# for agent in model_run_PE.schedule.agent_buffer(shuffled=False):
					# 	if isinstance(agent, ActiveAgent):
					# 		print(' ')
					# 		print(agent.agent_type, '\n', 'ID', agent.unique_id, 'Aff', agent.affiliation,
				# 		agent.issuetree[agent.unique_id], '\n',
					# 		agent.policytree[agent.unique_id])

				# output of the data

				# policy emergence model
				PE_save = PE_type[sce_i][0]
				if len(PE_type[sce_i]) > 0:
					for i in range(len(PE_type[sce_i])-1):
						PE_save += PE_type[sce_i][i+1]

				output_PE_model = model_run_PE.datacollector.get_model_vars_dataframe()
				output_PE_model.to_csv('O_PE_model_' + str(demand_growth[demand_ite])
									   + '_Sce' + str(sce_i) + '_Run' + str(rep_runs)
									   + '_type' + str(PE_save) + '.csv')
				output_PE_agents = model_run_PE.datacollector.get_agent_vars_dataframe()
				output_PE_agents.to_csv('O_PE_agents_' + str(demand_growth[demand_ite])
										+ '_Sce' + str(sce_i) + '_Run' + str(rep_runs)
										+ '_type' + str(PE_save) + '.csv')

				# policy context model
				output_policyContext_model = model_run_elec.datacollector.get_model_vars_dataframe()
				output_policyContext_model.to_csv('O_E1_model_' + str(demand_growth[demand_ite])
												  + '_Sce' + str(sce_i) + '_Run' + str(rep_runs)
												  + '_type'  + str(PE_save) +'.csv')