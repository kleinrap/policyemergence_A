import random
import copy
import pandas as pd

# from model_PE_agents import ActiveAgent, ElectorateAgent, TruthAgent

def inputs(sce_number):



    return PE_type, repetitions_runs, sce_number, PE_agents, PE_aff, res_aff, repr, goal_prof, w_el_inf, AplusPL_param, AplusCo_inputs

def read_inputs_beliefs(res_aff, number, time):

    input_goalProfiles_file = 'input_goalProfiles_Ex' + str(number) + str(time)
    goal_input = pd.read_csv(input_goalProfiles_file, sep=',')
    goal_profiles = []
    for i in range(len(res_aff[0]) * 2):
        goal_profiles.append(goal_input.iloc[i].tolist())  # goal profiles for active agents and electorate

    return goal_profiles