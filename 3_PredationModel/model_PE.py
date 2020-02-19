from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector

import copy
import random
from collections import defaultdict

from model_PE_agents_initialisation import init_active_agents, init_electorate_agents, init_truth_agent, \
	issuetree_creation, policytree_creation
from model_PE_agents import ActiveAgent, ElectorateAgent, TruthAgent, Coalition
from model_module_interface import policy_instrument_input, belief_tree_input

# Data collector function

def get_agents_attributes(model):
	'''
	Function used to record the agent attributes for the mesa datacollector.

	Note the need for deepcopy not to overwrite data each time.
	'''

	agent_attributes = []
	for agent in model.schedule.agent_buffer(shuffled=False):
		if isinstance(agent, ActiveAgent) and not isinstance(agent, Coalition):
			selected_PC = copy.deepcopy(agent.selected_PC)
			selected_S = copy.deepcopy(agent.selected_S)
			selected_PI = copy.deepcopy(agent.selected_PI)
			issuetree = copy.deepcopy(agent.issuetree[agent.unique_id])

			agent_attributes.append(
				[agent.unique_id, agent.agent_type, agent.affiliation, selected_PC, selected_S, selected_PI, issuetree])

	return agent_attributes

def get_coalitions_attributes(model):
	'''
	Function used to record the coalition attributes for the mesa datacollector.

	Note the need for deepcopy not to overwrite data each time.
	'''

	coalition_attributes = []
	for coalition in model.schedule.agent_buffer(shuffled=False):
		if isinstance(coalition, Coalition):
			selected_PC = copy.deepcopy(coalition.selected_PC)
			selected_S = copy.deepcopy(coalition.selected_S)
			selected_PI = copy.deepcopy(coalition.selected_PI)
			issuetree = copy.deepcopy(coalition.issuetree[model.number_activeagents])
			members = []
			for agent_mem in coalition.members:
				members.append(copy.deepcopy(agent_mem.unique_id))
			resources = copy.deepcopy(coalition.resources)

			coalition_attributes.append(
				[model.coa_resources_share, model.coa_creation_thresh, coalition.unique_id, selected_PC, selected_S,
				 selected_PI, issuetree, resources, members])

	return coalition_attributes

def get_electorate_attributes(model):
	'''
	Function used to record the electorate attributes for the mesa datacollector.

	Note the need for deepcopy not to overwrite data each time.
	'''

	agent_attributes = []
	for agent in model.schedule.agent_buffer(shuffled=False):
		if isinstance(agent, ElectorateAgent):
			representativeness = copy.deepcopy(agent.representativeness)
			issuetree = copy.deepcopy(agent.issuetree_elec)
			agent_attributes.append([agent.affiliation, representativeness, issuetree])

	return agent_attributes

def get_problem_policy_chosen(model):
	'''
	Function used to record the agenda and policy implemented for the mesa datacollector.

	Note the need for deepcopy not to overwrite data each time.
	'''

	return [model.agenda_PC, model.policy_implemented_number]

class PolicyEmergenceSM(Model):
	'''
	Simplest Model for the policy emergence model.
	'''

	def __init__(self, PE_type, SM_inputs, AplusPL_inputs, AplusCo_inputs, AplusPK_inputs, height=20, width=20, input_LHS=False):

		self.height = height # height of the canvas
		self.width = width # width of the canvas

		self.SM_inputs = SM_inputs # inputs for the entire model
		self.PE_type = PE_type # model type (SM, A+PL, A+Co, A+PK, A+PI)

		self.resources_aff = SM_inputs[2]  # resources per affiliation agent

		self.stepCount = 0 # int - [-] - initialisation of step counter
		self.agenda_PC = None # initialisation of agenda policy core issue tracker
		self.policy_implemented_number = None # initialisation of policy number tracker
		self.policy_formulation_run = False  # check value for running policy formulation

		self.w_el_influence = self.SM_inputs[5]  # float - [-] - electorate influence weight constant

		# batchrunner inputs
		self.input_LHS = input_LHS

		# ACF+PL parameters
		if 'A+PL' in self.PE_type or 'A+Co' in self.PE_type:
			self.conflict_level = AplusPL_inputs[0]
			self.resources_spend_incr_agents = AplusPL_inputs[1]

		# ACF+Co parameters
		if 'A+Co' in self.PE_type:
			self.PC_interest = AplusCo_inputs[0]
			if self.input_LHS:
				self.coa_creation_thresh = self.input_LHS[1]  # LHS inputs
				self.coa_resources_share = self.input_LHS[0]  # LHS inputs
			else:
				self.coa_creation_thresh = AplusCo_inputs[1]
				self.coa_resources_share = AplusCo_inputs[3]
			self.coa_coherence_thresh = AplusCo_inputs[2]
			self.resources_spend_incr_coal = AplusCo_inputs[4]
			print('res. share:', round(self.coa_resources_share,3), ', coa. threshold:', round(self.coa_creation_thresh,3))

			self.coalition_list = []

		# +PK parameters
		self.PK = False
		if '+PK' in self.PE_type:
			self.PK = True
		self.PK_catchup = AplusPK_inputs[0]

		self.schedule = RandomActivation(self) # mesa random activation method
		self.grid = SingleGrid(height, width, torus=True) # mesa grid creation method

		# creation of the datacollector vector

		if 'A+Co' in self.PE_type:
			self.datacollector = DataCollector(
				# Model-level variables
				model_reporters =  {
					"step": "stepCount",
					"AS_PF": get_problem_policy_chosen,
					"agent_attributes": get_agents_attributes,
					"coalitions_attributes": get_coalitions_attributes,
					"electorate_attributes": get_electorate_attributes},
				# Agent-level variables
				agent_reporters = {
					"x": lambda a: a.pos[0],
					"y": lambda a: a.pos[1],
					"Agent type": lambda a:type(a),
					"Issuetree": lambda a: getattr(a, 'issuetree', [None])[a.unique_id
					if isinstance(a, ActiveAgent) and not isinstance(a, Coalition) else 0]}
				)
		else:
			self.datacollector = DataCollector(
				# Model-level variables
				model_reporters={
					"step": "stepCount",
					"AS_PF": get_problem_policy_chosen,
					"agent_attributes": get_agents_attributes,
					"electorate_attributes": get_electorate_attributes},
				# Agent-level variables
				agent_reporters={
					"x": lambda a: a.pos[0],
					"y": lambda a: a.pos[1],
					"Agent type": lambda a: type(a),
					"Issuetree": lambda a: getattr(a, 'issuetree', [None])[
						a.unique_id if isinstance(a, ActiveAgent) else 0]}
			)


		self.len_S, self.len_PC, self.len_DC, self.len_CR = belief_tree_input() # setting up belief tree
		self.policy_instruments, self.len_ins, self.PF_indices = policy_instrument_input() # setting up policy instruments
		init_active_agents(self, self.len_S, self.len_PC, self.len_DC, self.len_CR, self.len_PC, self.len_ins,
						   self.SM_inputs) # setting up active agents
		init_electorate_agents(self, self.len_S, self.len_PC, self.len_DC, self.SM_inputs) # setting up passive agents
		init_truth_agent(self, self.len_S, self.len_PC, self.len_DC, self.len_ins) # setting up truth agent

		self.running = True
		self.numberOfAgents = self.schedule.get_agent_count()
		self.datacollector.collect(self)

	def step(self, KPIs):
		'''
		Main steps of the Simplest Model for policy emergence:
		0. Module interface - Input
		1. Agenda setting step
		2. Policy formulation step
		3. Data collection
		'''

		self.KPIs = KPIs # saving the indicators

		# 0. initialisation
		self.module_interface_input(self.KPIs) # communicating the beliefs (indicators)
		self.electorate_influence(self.w_el_influence) # electorate influence actions
		if 'A+Co' in self.PE_type:
			self.coalition_creation_algorithm()

		# 1. agenda setting
		self.agenda_setting()

		# 2. policy formulation
		if self.policy_formulation_run:
			policy_implemented = self.policy_formulation()
		else:
			policy_implemented = self.policy_instruments[-1]

		# 3. data collection
		self.stepCount += 1 # iterate the steps counter
		self.datacollector.collect(self) # collect data

		print("Step ends", "\n")

		return policy_implemented

	def module_interface_input(self, KPIs):

		'''
		The module interface input step consists of actions related to the module interface and the policy emergence model
		'''

		len_DC = self.len_DC; len_PC = self.len_PC; len_S = self.len_S; len_ins = self.len_ins

		# saving the issue tree of the truth agent
		for agent in self.schedule.agent_buffer(shuffled=True):
			if isinstance(agent, TruthAgent):
				agent.issuetree_truth = KPIs
				truth_issuetree = agent.issuetree_truth
				truth_policytree = agent.policytree_truth

		# Transferring policy impact to active agents
		for agent in self.schedule.agent_buffer(shuffled=True):
			if isinstance(agent, ActiveAgent) and not isinstance(agent, Coalition): # selecting only active agents
				# for PFj in range(len_PC): # communicating the policy family likelihoods
				# 	for PFij in range(len_PC):
				# 		agent.policytree[agent.unique_id][PFj][PFij] = truth_policytree[PFj][PFij]

				for insj in range(len_ins): # communicating the policy instruments impacts
					agent.policytree[agent.unique_id][len_PC + insj][0:len_S] = truth_policytree[len_PC + insj]

				for issue in range(len_DC + len_PC + len_S): # communicating the issue beliefs from the KPIs
					agent.issuetree[agent.unique_id][issue][0] = truth_issuetree[issue]
				self.preference_update(agent, agent.unique_id) # updating the preferences

	def resources_distribution(self):

		if 'A+PL' in self.PE_type or 'A+Co' in self.PE_type:
			for agent in self.schedule.agent_buffer(shuffled=False):
				if isinstance(agent, ActiveAgent):  # selecting only active agents
					if agent.affiliation == 0: # affiliation 0
						agent.resources = 0.01 * self.number_activeagents * self.resources_aff[0]/100
					if agent.affiliation == 1: # affiliation 1
						agent.resources = 0.01 * self.number_activeagents * self.resources_aff[1]/100
					agent.resources_action = agent.resources  # assigning resources for the actions for both
		if 'A+Co' in self.PE_type: # attribution of the resources to coalitions
			for coalition in self.schedule.agent_buffer(shuffled=False):
				if isinstance(coalition, Coalition):
					resources = 0
					for agent_mem in coalition.members:
						resources += agent_mem.resources * self.coa_resources_share
						agent_mem.resources -= self.coa_resources_share * agent_mem.resources
						agent.resources_action = agent.resources  # assigning resources for the actions for both
					coalition.resources = resources
					coalition.resources_action = coalition.resources  # assigning resources for the actions for both

	def agenda_setting(self):

		'''
		In the agenda setting step, the active agents first select their policy core issue of preference and then select
		the agenda.
		'''

		# resources distribution
		self.resources_distribution()

		# active agent policy core selection
		for agent in self.schedule.agent_buffer(shuffled=False):
			if isinstance(agent, ActiveAgent):  # selecting only active agents
				agent.selection_PC()

		if 'A+Co' in self.PE_type:
			for coalition in self.schedule.agent_buffer(shuffled=True):
				if isinstance(coalition, Coalition): # selecting only coalitions
					coalition.interactions_intra_coalition('AS') # intra-coalition interactions

		# active agent interactions (including coalitions)
		if 'A+PL' in self.PE_type or 'A+Co' in self.PE_type:
			for agent in self.schedule.agent_buffer(shuffled=True):
				if isinstance(agent, ActiveAgent):  # selecting only active agents
					agent.interactions('AS', self.PK)

		# active agent policy core selection (after agent interactions)
		if 'A+PL' in self.PE_type or 'A+Co' in self.PE_type:
			# active agent policy core selection
			for agent in self.schedule.agent_buffer(shuffled=False):
				if isinstance(agent, ActiveAgent):  # selecting only active agents
					agent.selection_PC()

		# for each agent, selection of their preferred policy core issue
		selected_PC_list = []
		number_ActiveAgents = 0
		for agent in self.schedule.agent_buffer(shuffled=False):
			if isinstance(agent, ActiveAgent):  # considering only policy makers
				selected_PC_list.append(agent.selected_PC)
				number_ActiveAgents += 1

		# finding the most common policy core issue and its frequency
		d = defaultdict(int)
		for i in selected_PC_list:
			d[i] += 1
		result = max(d.items(), key=lambda x: x[1])
		agenda_PC_temp = result[0]
		agenda_PC_temp_frequency = result[1]

		# checking for majority
		if agenda_PC_temp_frequency > int(number_ActiveAgents / 2):
			self.agenda_PC = agenda_PC_temp
			self.policy_formulation_run = True # allowing for policy formulation to happen
			print("The agenda consists of PC", self.agenda_PC, ".")
		else: # if no majority
			self.policy_formulation_run = False
			print("No agenda was formed, moving to the next step.")

		# for purposes of not changing the entire code - the policy family selected is set at 0 so all policy instruments
		# are always considered in the rest of the model
		self.agenda_PF = 0

	def policy_formulation(self):

		'''
		In the policy formulation step, the policy maker agents first select their policy core issue of preference and then
		they select the policy that is to be implemented if there is a majority of them.
		'''

		# resources distribution
		self.resources_distribution()

		# calculation of policy instruments preferences
		if 'A+PL' in self.PE_type or 'A+Co' in self.PE_type:
			for agent in self.schedule.agent_buffer(shuffled=False):
				if isinstance(agent, ActiveAgent):
					agent.selection_S()
					agent.selection_PI()  # individual agent policy instrument selection

		if 'A+Co' in self.PE_type:
			for coalition in self.schedule.agent_buffer(shuffled=True):
				if isinstance(coalition, Coalition): # selecting only active agents
					# print('selected_PC', agent.selected_PC)
					coalition.interactions_intra_coalition('PF')
					# coalition.interactions('PF')

		# active agent interactions
		if 'A+PL' in self.PE_type or 'A+Co' in self.PE_type:
			for agent in self.schedule.agent_buffer(shuffled=True):
				if isinstance(agent, ActiveAgent):  # selecting only active agents
					agent.interactions('PF', self.PK)

		# calculation of policy instruments preferences
		selected_PI_list = []
		number_PMs = 0
		for agent in self.schedule.agent_buffer(shuffled=False):
			if isinstance(agent, ActiveAgent) and agent.agent_type == 'policymaker':  # considering only policy makers
				agent.selection_S()
				agent.selection_PI() # individual agent policy instrument selection
				selected_PI_list.append(agent.selected_PI) # appending the policy instruments selected to a list for all PMs
				number_PMs += 1

		# finding the most common policy instrument and its frequency
		d = defaultdict(int)
		print(selected_PI_list)
		for i in selected_PI_list:
			d[i] += 1
		result = max(d.items(), key=lambda x: x[1])
		self.policy_implemented_number = result[0]
		policy_implemented_number_frequency = result[1]

		# check for the majority and implemented if satisfied
		if policy_implemented_number_frequency > int(number_PMs / 2):
			print("The policy selected is policy instrument ", self.policy_implemented_number, ".")
			policy_implemented = self.policy_instruments[self.policy_implemented_number]
		else: # if no majority
			print("No consensus on a policy instrument.")
			policy_implemented = self.policy_instruments[-1] # selecting status quo policy instrument

		return policy_implemented

	def preference_update(self, agent, who, coalition_check=False):

		'''
		This function is used to call the preference update functions of the issues of the active agents.
		'''


		if coalition_check:
			who = self.number_activeagents

		self.preference_update_DC(agent, who) # deep core issue preference update
		self.preference_update_PC(agent, who) # policy core issue preference update
		self.preference_update_S(agent, who) #

	def preference_update_DC(self, agent, who):

		"""
		This function is used to update the preferences of the deep core issues of agents in their
		respective issue trees.

		agent - this is the owner of the issue tree
		who - this is the part of the issuetree that is considered - agent.unique_id should be used for this -
		this is done to also include partial knowledge preference calculation
		"""

		len_DC = self.len_DC

		# calculation of the denominator
		PC_denominator = 0
		for h in range(len_DC):
			issue_belief = agent.issuetree[who][h][0]
			issue_goal = agent.issuetree[who][h][1]
			gap = issue_goal - issue_belief
			if issue_goal is not None and issue_belief is not None:
				PC_denominator += abs(gap)

		# selection of the numerator and calculation of the preference
		for i in range(len_DC):
			issue_belief = agent.issuetree[who][i][0]
			issue_goal = agent.issuetree[who][i][1]
			gap = issue_goal - issue_belief
			if PC_denominator != 0: # make sure the denominator is not 0
				agent.issuetree[who][i][2] = abs(gap) / PC_denominator
			else:
				agent.issuetree[who][i][2] = 0

	def preference_update_PC(self, agent, who):

		"""
		This function is used to update the preferences of the policy core issues of agents in their
		respective issue trees.

		agent - this is the owner of the belief tree
		who - this is the part of the issuetree that is considered - agent.unique_id should be used for this -
		this is done to also include partial knowledge preference calculation
		"""

		len_DC = self.len_DC; len_PC = self.len_PC; len_S = self.len_S

		PC_denominator = 0
		# calculation of the denominator
		for j in range(len_PC): # selecting the causal relations starting from PC

			for k in range(len_DC):
				cr = agent.issuetree[who][len_DC + len_PC + len_S + j + (k * len_PC)][0]
				issue_belief = agent.issuetree[who][k][0]
				issue_goal = agent.issuetree[who][k][1]
				gap = issue_goal - issue_belief
				if issue_goal is not None and issue_belief is not None and cr is not None \
						and ((cr < 0 and gap < 0) or (cr > 0 and gap > 0)):
					# contingency for partial knowledge issues and check if cr and belief-goal are same sign
					PC_denominator = PC_denominator + abs(cr * gap)

		# addition of the gaps of the associated mid-level issues
		for i in range(len_PC):
			issue_belief = agent.issuetree[who][len_DC + i][0]
			issue_goal = agent.issuetree[who][len_DC + i][1]
			gap = issue_goal - issue_belief
			if issue_goal is not None and issue_belief is not None: # contingency for partial knowledge issues
				PC_denominator += abs(gap)

		# calculation the numerator and the preference
		for j in range(len_PC): # select one by one the PC

			# calculation of the right side of the numerator
			PC_numerator = 0
			for k in range(len_DC): # selecting the causal relations starting from DC
				issue_belief = agent.issuetree[who][k][0]
				issue_goal = agent.issuetree[who][k][1]
				cr = agent.issuetree[who][len_DC + len_PC + len_S + j + (k * len_PC)][0]
				gap = issue_goal - issue_belief
				if issue_goal is not None and issue_belief is not None and cr is not None \
						and ((cr < 0 and gap < 0) or (cr > 0 and gap > 0)):
					# contingency for partial knowledge issues and check if cr and belief-goal are same sign
					PC_numerator += abs(cr * gap)

			# addition of the gap to the numerator
			issue_belief = agent.issuetree[who][len_DC + j][0]
			issue_goal = agent.issuetree[who][len_DC + j][1]
			gap = issue_goal - issue_belief
			if issue_goal is not None and issue_belief is not None: # contingency for partial knowledge issues
				PC_numerator += abs(gap)

			# calculation of the preferences
			if PC_denominator != 0:
				agent.issuetree[who][len_DC + j][2] = round(PC_numerator / PC_denominator,3)
			else:
				agent.issuetree[who][len_DC + j][2] = 0

	def preference_update_S(self, agent, who):

		"""
		This function is used to update the preferences of secondary issues the agents in their
		respective issue trees.

		agent - this is the owner of the belief tree
		who - this is the part of the issuetree that is considered - agent.unique_id should be used for this -
		this is done to also include partial knowledge preference calculation
		"""

		len_DC = self.len_DC; len_PC = self.len_PC; len_S = self.len_S

		S_denominator = 0
		# calculation of the denominator
		for j in range(len_S):

			for k in range(len_PC): # selecting the causal relations starting from S
				issue_belief = agent.issuetree[who][len_DC + k][0]
				issue_goal = agent.issuetree[who][len_DC + k][1]
				cr = agent.issuetree[who][len_DC + len_PC + len_S + len_DC* len_PC + j + (k * len_S)][0]
				gap = issue_goal - issue_belief
				if issue_goal is not None and issue_belief is not None and cr is not None \
						and ((cr < 0 and gap < 0) or (cr > 0 and gap > 0)):
					# contingency for partial knowledge issues and check if cr and belief-goal are same sign
					S_denominator += abs(cr * gap)

		# addition of the gaps of the associated secondary issues
		for j in range(len_S):
			issue_belief = agent.issuetree[who][len_DC + len_PC + j][0]
			issue_goal = agent.issuetree[who][len_DC + len_PC + j][1]
			# print(issue_goal, type(issue_goal), type(issue_belief))
			gap = issue_goal - issue_belief
			if issue_goal is not None and issue_belief is not None: # contingency for partial knowledge issues
				S_denominator += abs(gap)

		# calculation the numerator and the preference
		for j in range(len_S): # select one by one the S

			# calculation of the right side of the numerator
			S_numerator = 0
			for k in range(len_PC): # selecting the causal relations starting from PC
				# Contingency for partial knowledge issues
				cr = agent.issuetree[who][len_DC + len_PC + len_S + len_DC * len_PC + j + (k * len_S)][0]
				issue_belief = agent.issuetree[who][len_DC + k][0]
				issue_goal = agent.issuetree[who][len_DC + k][1]
				gap = issue_goal - issue_belief
				if issue_goal is not None and issue_belief is not None and cr is not None \
						and ((cr < 0 and gap < 0) or (cr > 0 and gap > 0)):
					# contingency for partial knowledge issues and check if cr and gap are same sign
					S_numerator += abs(cr * gap)

			# addition of the gap to the numerator
			issue_belief = agent.issuetree[who][len_DC + len_PC + j][0]
			issue_goal = agent.issuetree[who][len_DC + len_PC + j][1]
			gap = issue_goal - issue_belief
			if issue_goal is not None and issue_belief is not None: # contingency for partial knowledge issues
				S_numerator += abs(gap)

			# calculation of the preferences
			if S_denominator != 0:
				agent.issuetree[who][len_DC + len_PC + j][2] = round(S_numerator / S_denominator,3)
			else:
				agent.issuetree[who][len_DC + len_PC + j][2] = 0

	def electorate_influence(self, w_el_influence):

		'''
		This function calls the influence actions in the electorate agent class.
		'''

		for agent in self.schedule.agent_buffer(shuffled=True):
			if isinstance(agent, ElectorateAgent):
				agent.electorate_influence(w_el_influence)

	def coalition_creation_algorithm(self):

		'''
		Function that is used to reset the coalitions at the beginning of each round
		A maximum of two coalitions are allowed. The agents have to be within a certain threshold of their goals to be
		assembled together.
		Note that the preferred states only are considered and not the actual beliefs of the actors - this could be a
		problem when considering the partial information case.

		:return:
		'''

		# resetting the coalitions before the creation of new ones
		for coalition in self.schedule.agent_buffer(shuffled=False):
			if isinstance(coalition, Coalition):
				self.schedule.remove(coalition)

		# saving the agents in a list with their belief values
		list_agents_1 = [] # active agent list
		for agent in self.schedule.agent_buffer(shuffled=False):
			if isinstance(agent, ActiveAgent):
				list_agents_1.append((agent, agent.issuetree[agent.unique_id][self.len_DC + self.PC_interest][1]))
		list_agents_1.sort(key = lambda x: x[1]) # sorting the list based on the goals

		# checking for groups for first coalition
		list_coalition_number = []
		for i in range(len(list_agents_1)):
			count = 0
			for j in range(len(list_agents_1)):
				if list_agents_1[i][1] - self.coa_creation_thresh <= list_agents_1[j][1] <= list_agents_1[i][1] + self.coa_creation_thresh:
					count += 1
			list_coalition_number.append(count)

		index = list_coalition_number.index(max(list_coalition_number)) # finding the grouping with the most member index

		list_coalition_members = []
		list_agents_2 = copy.copy(list_agents_1)
		for i in range(len(list_agents_1)):
			if list_agents_1[index][1] - self.coa_creation_thresh <= list_agents_1[i][1] <= list_agents_1[index][1] + self.coa_creation_thresh:
				list_coalition_members.append(list_agents_1[i][0])
				list_agents_2.remove(list_agents_1[i])

		self.coalition_creation(1001, list_coalition_members) # creating the coalition with the selected members

		if len(list_agents_2) > 2: #check if there are enough agents left:

			# checking for groups for second coalition
			list_coalition_number = []
			for i in range(len(list_agents_2)):
				count = 0
				for j in range(len(list_agents_2)):
					if list_agents_2[i][1] - self.coa_creation_thresh <= list_agents_2[j][1] <= list_agents_2[i][1] + self.coa_creation_thresh:
						count += 1
				list_coalition_number.append(count)
			index = list_coalition_number.index(max(list_coalition_number)) # finding the grouping with the most member index

			list_coalition_members = []
			for i in range(len(list_agents_2)):
				if list_agents_2[index][1] - self.coa_creation_thresh <= list_agents_2[i][1] <= list_agents_2[index][1] + self.coa_creation_thresh:
					list_coalition_members.append(list_agents_2[i][0])

			self.coalition_creation(1002, list_coalition_members) # creating the coalition with selected members

	def coalition_creation(self, unique_id, members):

		'''
		Function that is used to create the object Coalition which is a sub-agent of the ActiveAgent class
		:param unique_id:
		:param members:
		:return:
		'''

		x = 0; y = 0; resources = 0 # resources are reset to 0
		len_DC = self.len_DC; len_PC = self.len_PC; len_S = self.len_S; len_CR = self.len_CR
		len_PF = self.len_PC; len_ins = self.len_ins

		issuetree_coal = [None] # creation of the issue tree
		issuetree_coal[0] = issuetree_creation(len_DC, len_PC, len_S, len_CR)  # using the newly made function
		for r in range(self.number_activeagents):  # last spot is where the coalition beliefs are stored
			issuetree_coal.append(issuetree_creation(len_DC, len_PC, len_S, len_CR))

		policytree_coal = [None] # creation of the policy tree
		policytree_coal[0] = members[0].policytree[members[0].unique_id]
		for r in range(self.number_activeagents):
			policytree_coal.append(members[0].policytree[members[0].unique_id])
		# note that the policy tree is simply copied ... this will not work in the case of partial information where a different
		# algorithm will need to be found for this part of the model

		# creation of the coalition agent
		agent = Coalition((x, y), unique_id, self, 'coalition', resources, 'X', issuetree_coal, policytree_coal, members)
		self.coalition_belief_update(agent, members)
		self.preference_update(agent, unique_id, True)  # updating the issue tree preferences
		self.grid.position_agent(agent, (x, y))
		self.schedule.add(agent)

	def coalition_belief_update(self, coalition, members):

		'''
		Function that is used to update the beliefs of the coalition to an average of the agents members of this said
		coalition.
		:param coalition:
		:param members:
		:return:
		'''

		len_DC = self.len_DC; len_PC = self.len_PC; len_S = self.len_S; len_CR = self.len_CR

		for k in range(len_DC + len_PC + len_S): # updating the preferred states and actual beliefs
			belief = 0
			goal = 0
			for agent_mem in members:
				id = agent_mem.unique_id
				belief += agent_mem.issuetree[id][k][0]
				goal += agent_mem.issuetree[id][k][1]
			coalition.issuetree[self.number_activeagents][k][0] = belief / len(members)
			coalition.issuetree[self.number_activeagents][k][1] = goal / len(members)

		for k in range(len_CR): # updating the causal relations
			CR = 0
			for agent_mem in members:
				id = agent_mem.unique_id
				CR += agent_mem.issuetree[id][len_DC + len_PC + len_S + k][0]
			coalition.issuetree[self.number_activeagents][len_DC + len_PC + len_S + k][0] = CR / len(members)

		if self.PK: # for the partial knowledge
			for agent in self.schedule.agent_buffer(shuffled=False):
				if agent not in members and isinstance(agent, ActiveAgent) and not isinstance(agent, Coalition):
					id = agent.unique_id
					for k in range(len_DC + len_PC + len_S): # updating the preferred states
						goal = 0
						for agent_mem in members:
							goal += agent_mem.issuetree[id][k][1]
						coalition.issuetree[id][k][1] = goal / len(members)

					for k in range(len_CR):  # updating the causal relations
						CR = 0
						for agent_mem in members:
							CR += agent_mem.issuetree[id][len_DC + len_PC + len_S + k][0]
						coalition.issuetree[id][len_DC + len_PC + len_S + k][0] = CR / len(members)