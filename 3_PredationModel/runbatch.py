# imports for the policy emergence model
from model_PE import PolicyEmergenceSM
from model_PE_policyImpact import policy_impact_evaluation
from model_PE_agents import ActiveAgent

# imports for the policy context model
from model_predation import WolfSheepPredation

# import other packages
import pandas as pd

def read_inputs(res_aff, number, name, time='', elec=False):
    param = 1
    if elec:
        param = 2
    input_name = 'input_'+ str(name) + 'Profiles_Ex' + str(number) + str(time)
    input_file = pd.read_csv(input_name, sep=',')
    profiles = []
    for i in range(len(res_aff[0]) * param):
        profiles.append(input_file.iloc[i].tolist())  # goal profiles for active agents and electorate

    return profiles

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

# todo notes:
#  - at the moment no agenda is ever created, after the introduction of the update of the active agents update
#    the initialisation of the beliefs for the external parties is crucial to the selection of an agenda - worth mentionning
#    in the discusion

# running parameters
total_ticks = 1600
interval_tick = 100
run_tick = int(total_ticks/interval_tick)
warmup_tick = interval_tick
sce_number = 17 # total number of scenarios

# batch run parameters
repetitions_runs = 50

PE_type = [['SM'], ['A+PL'], ['A+PL'], ['A+PL'], ['A+PL'], # +PL
           ['A+Co'], ['A+Co'], ['A+Co'], ['A+Co'], # +Co
           ['A+PL', '+PK'], ['A+Co', '+PK'], # +PK
           ['A+PL', '+PI'], ['A+Co', '+PI'], ['A+PL', '+PI'], ['A+PL', '+PI'], ['A+PL', '+PI'], ['A+PL', '+PI']] # +PI

# parameters of the policy context model
'''
Here go all the parameters that are needed to initialise the policy context model
'''

# parameters of the policy emergence model
'''for all scenarios'''

# resources per affiliation agent out of 100
res_aff = [[75, 25] for p in range(sce_number)]
res_aff[2] = [10, 100]  # changed for scenario 2

# electorate representativeness per affiliation
repr = [[25, 75] for p in range(sce_number)]

# list - [-] - electorate influence weight constant [per scenario]
w_el_inf = [0 for p in range(sce_number)]

'''actor distribution'''
PE_PMs_0 = 3  # number of policy makers
PE_PEs_0 = 8  # number of policy entrepreneurs
PE_EPs_0 = 0  # number of external parties
PE_agents = [[PE_PMs_0, PE_PEs_0, PE_EPs_0] for p in range(sce_number)]
PE_agents[11][2] = 2 # adding external parties for the +PI scenario
PE_agents[12][2] = 2 # adding external parties for the +PI scenario
PE_agents[13][2] = 2 # adding external parties for the +PI scenario
PE_agents[14][2] = 2 # adding external parties for the +PI scenario
PE_agents[15][2] = 2 # adding external parties for the +PI scenario
PE_agents[16][2] = 2 # adding external parties for the +PI scenario

PE_PMs_aff_0 = [2, 1]  # policy maker distribution per affiliation
PE_PEs_aff_0 = [4, 4]  # policy entrepreneur distribution per affiliation
PE_EPs_aff_0 = [0, 0]  # external parties distribution per affiliation
PE_aff = [[PE_PMs_aff_0, PE_PEs_aff_0, PE_EPs_aff_0] for p in range(sce_number)]
PE_aff[11][2] = [1, 1]
PE_aff[12][2] = [1, 1]
PE_aff[13][2] = [1, 1]
PE_aff[14][2] = [1, 1]
PE_aff[15][2] = [1, 1]
PE_aff[16][2] = [1, 1]

# input profile for preferred states
'''
This can be used for different scenarios for the preferred states (goals) of the policy emergence agents
'''

goal_prof = []
goal_prof_after = []
event = [False for p in range(sce_number)]
event[3] = True
event[4] = True
for i in range(sce_number):
    goal_prof.append(read_inputs(res_aff, i, 'goal', 'Be', True))
    if not event[i]: # making sure that only event related scenarios are added
        goal_prof_after.append([])
    if event[i]:
        goal_prof.append(read_inputs(res_aff, i, 'goal', 'Af', True))

# ACF + PL parameters
con_lvl = [0.50, 0.75, 0.25]  # conflict levels [low, mid, high]
resources_spend_incr_agents = 0.10  # percentage of the resources spent by the agents for interactions
AplusPL_param = [con_lvl, resources_spend_incr_agents]

# ACF + Co parameters
PC_interest = [0 for p in range(sce_number)] # issue number around which coalitions assemble
PC_interest[6] = 1
PC_interest[7] = 2
coa_creation_thresh = 0.15  # threshold belief difference to create coalitions
coa_coherence_thresh = 0.10  # threshold belief difference to trigger coalition intra-actions
coa_resources_share = 0.50  # amount of resources assigned to coalitions from agents in coalitions
resources_spend_incr_coal = 0.05  # percentage of the resources spent by the coalition for interactions

# +PK parameters
PK_catchup = 0.20
AplusPK_inputs = [PK_catchup]

# +PI parameters
bias_inputs = []
belief_inputs = []
for i in range(sce_number):
    if '+PI' not in PE_type[i]:
        bias_inputs.append([])
        belief_inputs.append([])
    else:
        bias_inputs.append(read_inputs(res_aff, i, 'bias'))
        belief_inputs.append(read_inputs(res_aff, i, 'belief'))
# aff.   same,different
w_aff = [[1.0, 0.75] for p in range(sce_number)] # trust affiliation matrix
w_aff[14] = [1.0, 0] # changing scenario 14 to remove inter-affiliation communications
w_aff[16] = [1.0, 0] # changing scenario 16 to remove inter-affiliation communications
# AplusPI_inputs = [] # in case there is no +PI model


print("\n")
# running a number of scenarios
''' changes in the agent distribution '''
# running a number of repetitions per experiment
for rep_runs in range(repetitions_runs):

    for sce_i in range(sce_number):

        PE_inputs = [PE_agents[sce_i], PE_aff[sce_i], res_aff[sce_i], repr[sce_i], goal_prof[sce_i], w_el_inf[sce_i]]

    # # running a number of repetitions per experiment
    # for rep_runs in range(repetitions_runs):

        # for model run tailoring
        if sce_i == 13:

            print("PE_type:", PE_type[sce_i])
            print('sce.:', sce_i)
            print('run:', rep_runs)
            print('w_el', w_el_inf[sce_i])
            print('PC_interest:', PC_interest[sce_i])

            # initialisation of the policy context model
            model_run_predation = WolfSheepPredation(50, 50, 100, 50, 0.04, 0.05, 30, True, 30, 4)

            AplusCo_inputs = [PC_interest[sce_i], coa_creation_thresh, coa_coherence_thresh, coa_resources_share,
                              resources_spend_incr_coal]
            AplusPI_inputs = [bias_inputs[sce_i], belief_inputs[sce_i], w_aff[sce_i]]

            # initialisation of the policy emergence model
            model_run_PE = PolicyEmergenceSM(PE_type[sce_i], PE_inputs, AplusPL_param, AplusCo_inputs, AplusPK_inputs,
                AplusPI_inputs, 10, 10)

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

                # scenario 3 - change in policy core preferred states affiliation 0
                if i == 3 and sce_i == 3:
                    # changing the electorate preferred states values based on the scenarios input
                    for agent in model_run_PE.schedule.agent_buffer(shuffled=True):
                        if isinstance(agent, ActiveAgent):
                            for issue in range(model_run_PE.len_DC + model_run_PE.len_PC + model_run_PE.len_S):
                                if agent.affiliation == 0:
                                    agent.issuetree[agent.unique_id][issue][1] = \
                                        goal_prof_after[sce_i][agent.affiliation][1 + issue]

                # scenario 4 - change in secondary preferred states affiliation 0
                if i == 3 and sce_i == 4:
                    # changing the electorate preferred states values based on the scenarios input
                    for agent in model_run_PE.schedule.agent_buffer(shuffled=True):
                        if isinstance(agent, ActiveAgent):
                            for issue in range(model_run_PE.len_DC + model_run_PE.len_PC + model_run_PE.len_S):
                                if agent.affiliation == 0:
                                    agent.issuetree[agent.unique_id][issue][1] = \
                                        goal_prof_after[sce_i][agent.affiliation][1 + issue]

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
            output_PE_model.to_csv('O_PE_model_Sce' + str(sce_i) + '_Run' + str(rep_runs)
                                   + '_type' + str(PE_save) + '.csv')
            output_PE_agents = model_run_PE.datacollector.get_agent_vars_dataframe()
            output_PE_agents.to_csv('O_PE_agents_Sce' + str(sce_i) + '_Run' + str(rep_runs)
                                    + '_type' + str(PE_save) + '.csv')

            # policy context model
            if PE_type != 'A+Co':
                output_policyContext_model = model_run_predation.datacollector.get_model_vars_dataframe()
                output_policyContext_model.to_csv('O_Pre_model_Sce' + str(sce_i) + '_Run' + str(rep_runs)
                                                  + '_type'  + str(PE_save) +'.csv')
            if PE_type == 'A+Co':
                output_policyContext_model = model_run_predation.datacollector.get_model_vars_dataframe()
                output_policyContext_model.to_csv('O_Pre_model_Sce' + str(sce_i) + '_Run' + str(rep_runs)
                                                  + '_type' + str(PE_save) + '_res_share'
                                                  + str(coa_resources_share)+ '.csv')