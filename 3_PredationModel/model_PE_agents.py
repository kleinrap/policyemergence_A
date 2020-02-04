from mesa import Agent
import copy
import random

class ActiveAgent(Agent):
    '''
    Active agents, including policy makers, policy entrepreneurs and external parties.
    '''
    def __init__(self, pos, unique_id, model, agent_type, resources, affiliation, issuetree, policytree):

        '''
         Args:
            unique_id: Unique identifier for the agent.
            x, y: Agent initial location.
            agent_type: Indicator for the agent's type (minority=1, majority=0)
        '''
        super().__init__(unique_id, model)
        self.pos = pos  # defines the position of the agent on the grid
        self.unique_id = unique_id  # unique_id of the agent used for algorithmic reasons
        self.agent_type = agent_type  # defines the type of agents from policymaker, policyentrepreneur and externalparty
        self.resources = resources  # resources used for agents to perform actions
        self.affiliation = affiliation  # political affiliation affecting agent interactions
        self.issuetree = issuetree  # issue tree of the agent (including partial issue of other agents)
        self.policytree = policytree # policy tree for future models

        self.selected_PC = None; self.selected_S = None; self.selected_PI = None  # selected issues and policies

    def selection_PC(self):

        '''
        This function is used to select the preferred policy core issue for the active agents based on all their
        preferences for the policy core issues.
        '''

        len_DC = self.model.len_DC; len_PC = self.model.len_PC; len_S = self.model.len_S

        # making sure the right unique_id is used in the case of a coalition
        if isinstance(self, Coalition):
            unique_id = self.model.number_activeagents
        else:
            unique_id = self.unique_id

        # compiling all the preferences
        PC_pref_list = [None for k in range(len_PC)]
        for i in range(len_PC):
            PC_pref_list[i] = self.issuetree[unique_id][len_DC + i][2]

        self.selected_PC = PC_pref_list.index(max(PC_pref_list))  # assigning the highest preference

    def selection_S(self):

        '''
        This function is used to select the preferred secondary issue. First, only the secondary issues that are
        related, through a causal relation, to the policy core issue on the agenda are placed into an array. Then,
        the one with the highest preference is selected. It is then used as the issue that the agent will advocate for
        later on.
        '''

        len_DC = self.model.len_DC; len_PC = self.model.len_PC; len_S = self.model.len_S

        # making sure the right unique_id is used in the case of a coalition
        if isinstance(self, Coalition):
            unique_id = self.model.number_activeagents
        else:
            unique_id = self.unique_id

        # considering only issues related to the issue on the agenda
        S_pref_list_indices = []
        for i in range(len_S):
            cr = len_DC + len_PC + len_S + len_DC * len_PC + self.model.agenda_PC * len_S + i
            if self.issuetree[unique_id][cr][0] != 0:
                S_pref_list_indices.append(i)

        S_pref_list = [None for i in range(len(S_pref_list_indices))]
        for i in range(len(S_pref_list)):
            S_pref_list[i] = self.issuetree[unique_id][len_DC + len_PC + S_pref_list_indices[i]][2]

        # assigning the highest preference as the selected policy core issue
        self.selected_S = S_pref_list.index(max(S_pref_list))
        # make sure to select the right value in the list of indices (and not based on the index in the list of preferences)
        self.selected_S = S_pref_list_indices[self.selected_S]

    def selection_PI(self):

        '''
        This function is used to select the preferred policy instrument from the policy family on the agenda. First the
        preferences are calculated. Then the policy family preferred is selected as the policy family with the lowest
        preference (this means the smallest gap after the introduction of the policy family likelihood).

        Note that the algorithm considers the PF version where the policy family selected is the one for containing all
        policy instruments - as policy families are not implemented in this version of the model. This is to avoid having
        to rewrite the entire code.
        '''

        len_DC = self.model.len_DC; len_PF = self.model.len_PC; len_PC = self.model.len_PC; len_S = self.model.len_S

        # making sure the right unique_id is used in the case of a coalition
        if isinstance(self, Coalition):
            unique_id = self.model.number_activeagents
        else:
            unique_id = self.unique_id

        # selecting the policy instrument from the policy family on the agenda
        PFIns_indices = copy.copy(self.model.PF_indices[self.model.agenda_PF])
        len_PFIns_indices = len(PFIns_indices)

        '''making sure not to include non-agenda related policies'''
        # finding a secondary issue not related to the agenda
        S_list_indices = []
        for i in range(len_S):
            cr = len_DC + len_PC + len_S + len_DC * len_PC + self.model.agenda_PC * len_S + i
            if -0.01 >= self.issuetree[unique_id][cr][0] >= 0.01:
            # if self.issuetree[unique_id][cr][0] >= -0.01 and self.issuetree[unique_id][cr][0] <= 0.01:
                S_list_indices.append(i)

        # finding a policy instrument only affecting the secondary issues selected above
        for PIj in range(len(PFIns_indices)): # going through all instruments
            i = 0 # starting counter for while loop
            inst_check = [] # make a list of all interaction between the instrument and the concerned secondary issues
            while i < len(S_list_indices): # checking the indices recorded

                Si = S_list_indices[i] # selecting the secondary issue
                inst_check.append(abs(self.policytree[unique_id][len_PF + PIj][Si])) # recording the impacts
                i += 1 # iterating the counter for the while loop

            # remove unnecessary policy instruments - check sum of recorded impacts
            if inst_check and 0.01 >= round(sum(inst_check),2) >= -0.01: # if almost 0, make sure instrument won't be selected.
                print('PI removed:', PIj)
                PFIns_indices.remove(PIj)

        '''policy instrument preference calculation'''
        # denominator
        PI_denominator = 0 # resetting denominator counter

        for PIj in PFIns_indices: # going through all policy instruments

            for Si in range(len_S): # going through all secondary issues
                state = self.issuetree[unique_id][len_DC + len_PC + Si][0]
                goal = self.issuetree[unique_id][len_DC + len_PC + Si][1]
                impact = self.policytree[unique_id][len_PF + PIj][Si]

                # print(self.policytree[unique_id])
                # print(impact)

                new_state = (state * (1 + impact))  # calculation of the impact of the instrument on the state
                gap = abs(goal - new_state)  # calculation of the goal-state gap

                PI_denominator += round(gap,3) # adding up to the denominator

        # numerator
        for PIj in PFIns_indices: # going through all policy instruments

            PI_numerator = 0 # resetting the numerator counter for each policy instrument
            for Si in range(len_S): # going through all secondary issues
                state = self.issuetree[unique_id][len_DC + len_PC + Si][0]
                goal = self.issuetree[unique_id][len_DC + len_PC + Si][1]
                impact = self.policytree[unique_id][len_PF + PIj][Si]

                new_state = (state * (1 + impact)) # calculation of the impact of the instrument on the state
                gap = abs(goal - new_state) # calculation of the goal-state gap

                PI_numerator += round(gap, 3) # adding up to the numerator (per policy instrument)

            self.policytree[unique_id][len_PF + PIj][len_S] = \
                round(PI_numerator/PI_denominator,3) # assigning the preference value (per policy instrument)

        '''selection of the preferred policy instrument'''
        # compiling all the preferences
        PI_pref_list = [1 for k in range(len_PFIns_indices)] # we use 1 as the lowest gap is selected later
        for PIj in PFIns_indices:
            PI_pref_list[PIj] = self.policytree[unique_id][len_PF + PIj][len_S]

        # assigning the lowest preference as the selected policy instrument by the agent
        # lowest gap is preferred for agents - hence lowest preference
        self.selected_PI = PI_pref_list.index(min(PI_pref_list))
        self.selected_PI = self.model.PF_indices[self.model.agenda_PF][self.selected_PI]

    def interactions_AS(self):

        """
        ACF+PL
        This function is used to perform the different agent interactions for the active agents during the
        agenda setting step.

        The interactions that can be performed are on the preferred states and on the causal beliefs.
        All of the actions are first graded based on conflict levels. Then the action that has the highest grade is
        selected. Finally, the action selected is implemented.
        """

        len_DC = self.model.len_DC; len_PC = self.model.len_PC; len_S = self.model.len_S
        action_number = len_DC + 1 # number of actions allowed in this step (causal beliefs, preferred states)

        # selection of the cw of interest
        cb_of_interest = []
        # consider only the causal relations related to the problem on the agenda
        for cb_choice in range(len_DC):
            cb_of_interest.append(len_DC + len_PC + len_S + self.selected_PC * len_PC + cb_choice)

        # assigning resources for the actions
        self.resources_action = self.resources

        # making sure there are enough resources
        while self.resources_action > 0.001:

            total_grade_list = [] # initialising the grade list
            total_agent_list = [] # initialising the agent list

            for target in self.model.schedule.agent_buffer(shuffled=True):  # going through the other agents
                if isinstance(target, ActiveAgent) and not isinstance(target, Coalition) \
                        and target != self:  # making sure it is an active agent and not a coalition and not self
                    total_agent_list.append(target.unique_id) # saving the agent considered (randomly selected)

                    # looking at causal beliefs
                    for i in range(len(cb_of_interest)): # go through all causal beliefs of interest
                        cb = cb_of_interest[i] # selecting the causal belief
                        value1 = self.issuetree[self.unique_id][cb][0]
                        value2 = target.issuetree[target.unique_id][cb][0]
                        conflict_level, diff = self.conflict_level_calc(value1, value2)
                        total_grade_list.append(conflict_level * abs(diff)/2)

                    # looking the preferred states (aka goal)
                    goal = len_DC + self.selected_PC # selecting the right goal
                    value1 = self.issuetree[self.unique_id][goal][1]
                    value2 = target.issuetree[target.unique_id][goal][1]
                    conflict_level, diff = self.conflict_level_calc(value1, value2) # calculating the conflict level
                    total_grade_list.append(conflict_level * diff)
            # print(total_agent_list)
            # print(total_grade_list)

            # selecting the best graded interaction
            max_best_action = max(total_grade_list)
            best_action_index = total_grade_list.index(max(total_grade_list)) # index of interaction in the list
            best_action_agent_id = total_agent_list[int(best_action_index/action_number)] # unique_id of interaction target
            # print(max_best_action, best_action_index, int(best_action_index/action_number), best_action_agent_id)

            best_action_type = best_action_index - action_number * int(best_action_index / action_number)
            # selecting the action type (0 is a causal belief action, 1 is a preferred state action)

            # performing the interaction
            for target in self.model.schedule.agent_buffer(shuffled=True):  # going through the other agents
                if target.unique_id == best_action_agent_id:  # making sure it is an active agent and not self
                    # print('Actor: #', self.unique_id, ', target: #', target.unique_id)
                    if best_action_type <= action_number - 1 - 1: # action type: causal belief
                        cb_choice = cb_of_interest[best_action_type]
                        target.issuetree[target.unique_id][cb_choice][0] += \
                        (self.issuetree[self.unique_id][cb_choice][0] -
                         target.issuetree[target.unique_id][cb_choice][0]) * (self.resources * 0.1)

                    if best_action_type == action_number - 1: # action type: preferred state
                        goal = len_DC + self.selected_PC
                        # print('Acting:', self.issuetree[self.unique_id][goal][1])
                        # print('Bf:', target.issuetree[target.unique_id][goal][1])
                        # print('Change', (self.issuetree[self.unique_id][goal][1] -
                        #      target.issuetree[target.unique_id][goal][1]) * (self.resources/100 * 0.1))
                        target.issuetree[target.unique_id][goal][1] += \
                            (self.issuetree[self.unique_id][goal][1] -
                             target.issuetree[target.unique_id][goal][1]) * (self.resources/100 * 0.1)
                        # print('Af:', target.issuetree[target.unique_id][goal][1])
                        # print(' ')

                    self.resources_action -= self.resources * 0.1 # removing the action resources

    def interactions_PF(self):

        """
        ACF+PL
        This function is used to perform the different agent interactions for the active agents during the
        policy formulation step.

        The interactions that can be performed are on the preferred states and on the causal beliefs.
        All of the actions are first graded based on conflict levels. Then the action that has the highest grade is
        selected. Finally, the action selected is implemented.
        """

        len_DC = self.model.len_DC; len_PC = self.model.len_PC; len_S = self.model.len_S
        action_number = len_PC + 1 # number of actions allowed in this step (causal beliefs, preferred states)

        # selection of the cw of interest
        cb_of_interest = []
        # consider only the causal relations related to the problem on the agenda
        for cb_choice in range(len_PC):
            cb_of_interest.append(len_DC + len_PC + len_S + len_DC * len_PC + self.selected_S * len_S + cb_choice)
        # print(cb_of_interest)
        # print(' ')

        # assigning resources for the actions
        self.resources_action = self.resources

        # making sure there are enough resources
        while self.resources_action > 0.001:

            total_grade_list = [] # initialising the grade list
            total_agent_list = [] # initialising the agent list

            for target in self.model.schedule.agent_buffer(shuffled=True):  # going through the other agents
                if isinstance(target, ActiveAgent) and not isinstance(target, Coalition) \
                        and target != self:  # making sure it is an active agent and not a coalition and not self
                    total_agent_list.append(target.unique_id) # saving the agent considered (randomly selected)

                    agent_type_bonus = 1 # making sure policymakers are preferred for the PF interactions
                    if target.agent_type == 'policymaker':
                        agent_type_bonus = 1.1

                    # looking at causal beliefs
                    for i in range(len(cb_of_interest)): # go through all causal beliefs of interest
                        cb = cb_of_interest[i] # selecting the causal belief
                        value1 = self.issuetree[self.unique_id][cb][0]
                        value2 = target.issuetree[target.unique_id][cb][0]
                        conflict_level, diff = self.conflict_level_calc(value1, value2)
                        total_grade_list.append(conflict_level * abs(diff)/2 * agent_type_bonus)
                        # the abs is needed to take care of the causal belief range of [-1, 1]
                        # the /2 is used also due to a range twice as large as for the other interactions

                    # looking the preferred states (aka goal)
                    goal = len_DC + len_PC + self.selected_S # selecting the right goal
                    value1 = self.issuetree[self.unique_id][goal][1]
                    value2 = target.issuetree[target.unique_id][goal][1]
                    conflict_level, diff = self.conflict_level_calc(value1, value2) # calculating the conflict level
                    total_grade_list.append(conflict_level * diff * agent_type_bonus)
            # print(total_agent_list)
            # print(total_grade_list)

            # selecting the best graded interaction
            max_best_action = max(total_grade_list)
            best_action_index = total_grade_list.index(max(total_grade_list)) # index of interaction in the list
            best_action_agent_id = total_agent_list[int(best_action_index/action_number)] # unique_id of interaction target
            # print(max_best_action, best_action_index, int(best_action_index/action_number), best_action_agent_id)

            best_action_type = best_action_index - action_number * int(best_action_index / action_number)
            # selecting the action type (0 is a causal belief action, 1 is a preferred state action)

            # performing the interaction
            for target in self.model.schedule.agent_buffer(shuffled=True):  # going through the other agents
                if target.unique_id == best_action_agent_id:  # making sure it is an active agent and not self
                    # print('Actor: #', self.unique_id, ', target: #', target.unique_id)
                    if best_action_type <= action_number - 1 - 1: # action type: causal belief
                        cb_choice = cb_of_interest[best_action_type]
                        target.issuetree[target.unique_id][cb_choice][0] += \
                        (self.issuetree[self.unique_id][cb_choice][0] -
                         target.issuetree[target.unique_id][cb_choice][0]) * (self.resources * 0.1)

                    if best_action_type == action_number - 1: # action type: preferred state
                        goal = len_DC + len_PC + self.selected_S
                        # print('Aff.', self.affiliation)
                        # print('Acting:', self.issuetree[self.unique_id][goal][1])
                        # print('Bf:', target.issuetree[target.unique_id][goal][1])
                        # print('Change', (self.issuetree[self.unique_id][goal][1] -
                        #      target.issuetree[target.unique_id][goal][1]) * (self.resources/100 * 0.1))
                        target.issuetree[target.unique_id][goal][1] += \
                            (self.issuetree[self.unique_id][goal][1] -
                             target.issuetree[target.unique_id][goal][1]) * (self.resources/100 * 0.1)
                        # print('Af:', target.issuetree[target.unique_id][goal][1])
                        # print(' ')

                    self.resources_action -= self.resources * 0.1 # removing the action resources

    def conflict_level_calc(self, value1, value2):

        '''
        Function used to calculate the conflict level
        :param value1:
        :param value2:
        :return:
        '''

        conflict_level_low = self.model.conflict_level[0]
        conflict_level_mid = self.model.conflict_level[1]
        conflict_level_hig = self.model.conflict_level[2]

        diff = abs(value1 - value2)

        if diff < 0.2:
            conflict_level = conflict_level_low
        if 0.2 <= diff <= 0.40:
            conflict_level = conflict_level_mid
        if diff > 0.40:
            conflict_level = conflict_level_hig

        return conflict_level, diff

    # def selection_PF(self):
    #
    #     '''
    #     This function is used to select the preferred policy family. First the preferences are calculated. Then the
    #     policy family preferred is selected as the policy family with the lowest preference (this means the smallest
    #     gap after the introduction of the policy family likelihood).
    #     '''
    #
    #     len_DC = self.model.len_DC
    #     len_PF = self.model.len_PC  # number of PC is always equal to number of PF
    #     len_PC = self.model.len_PC
    #     len_S = self.model.len_S
    #
    #     # calculation of the preferences for all policy families
    #     # calculation of the denominator
    #     PF_denominator = 0
    #     # going through all policy families
    #     for PFj in range(len_PF):
    #         # going through all policy core issues
    #         for PCi in range(len_PC):
    #             gap = 0
    #             # print(" ")
    #             # print(PFj, PCi)
    #             # print(self.policytree[self.unique_id][PFj])
    #             # print(self.policytree[self.unique_id][PFj][PCi])
    #             # check if the likelihood is positive
    #             if self.policytree[self.unique_id][PFj][PCi] > 0:
    #                 # calculating the gap
    #                 # gap = self.issuetree[self.unique_id][len_DC+PCi][1] - self.issuetree[self.unique_id][len_DC+PCi][0]
    #                 # print("Before: ", gap)
    #                 gap = abs(self.issuetree[self.unique_id][len_DC+PCi][1] -
    #                 (self.issuetree[self.unique_id][len_DC+PCi][0] * (1 + self.policytree[self.unique_id][PFj][PCi])))
    #                 # print("After: ", gap)
    #             # check if the likelihood is negative
    #             if self.policytree[self.unique_id][PFj][PCi] < 0:
    #                 # gap = self.issuetree[self.unique_id][len_DC+PCi][1] - self.issuetree[self.unique_id][len_DC+PCi][0]
    #                 # print("Before: ", gap)
    #                 # calculating the gap
    #                 gap = abs(self.issuetree[self.unique_id][len_DC+PCi][1] -
    #                 (self.issuetree[self.unique_id][len_DC+PCi][0] * abs(self.policytree[self.unique_id][PFj][PCi])))
    #                 # print("After: ", gap)
    #             PF_denominator += round(gap,3)
    #             # print("PF_denominator: ", PF_denominator)
    #
    #     # calculation of the numerator
    #     # going through all policy families
    #     for PFj in range(len_PF):
    #         PF_numerator = 0
    #         # going through all policy core issues
    #         for PCi in range(len_PC):
    #             gap = 0
    #             # print(" ")
    #             # print(PFj, PCi)
    #             # print(self.policytree[self.unique_id][PFj])
    #             # print(self.policytree[self.unique_id][PFj][PCi])
    #             # check if the likelihood is positive
    #             if self.policytree[self.unique_id][PFj][PCi] > 0:
    #                 # calculating the gap
    #                 # gap = self.issuetree[self.unique_id][len_DC+PCi][1] - self.issuetree[self.unique_id][len_DC+PCi][0]
    #                 # print("Before: ", gap)
    #                 gap = abs(self.issuetree[self.unique_id][len_DC+PCi][1] -
    #                 (self.issuetree[self.unique_id][len_DC+PCi][0] * (1 + self.policytree[self.unique_id][PFj][PCi])))
    #                 # print("After: ", gap)
    #             # check if the likelihood is negative
    #             if self.policytree[self.unique_id][PFj][PCi] < 0:
    #                 # gap = self.issuetree[self.unique_id][len_DC+PCi][1] - self.issuetree[self.unique_id][len_DC+PCi][0]
    #                 # print("Before: ", gap)
    #                 # calculating the gap
    #                 gap = abs(self.issuetree[self.unique_id][len_DC+PCi][1] -
    #                 (self.issuetree[self.unique_id][len_DC+PCi][0] * abs(self.policytree[self.unique_id][PFj][PCi])))
    #                 # print("After: ", gap)
    #             PF_numerator += round(gap,3)
    #         self.policytree[self.unique_id][PFj][len_PC] = round(PF_numerator/PF_denominator,3)
    #     #     print(self.issuetree[self.unique_id][PFj])
    #     # print(self.issuetree[self.unique_id])
    #
    #     # selection of the preferred policy family
    #     # compiling all the preferences
    #     PF_pref_list = [None for k in range(len_PC)]
    #     for i in range(len_PC):
    #         PF_pref_list[i] = self.policytree[self.unique_id][i][len_PC]
    #
    #     # assigning the lowest preference as the selected policy family by the agent
    #     self.selected_PF = PF_pref_list.index(min(PF_pref_list))

class Coalition(ActiveAgent):

    # todo - adapt the coalition class

    '''
    Active agents, including policy makers, policy entrepreneurs and external parties.
    '''
    def __init__(self, pos, unique_id, model, agent_type, resources, affiliation, issuetree, policytree, members):

        '''
         Args:
            unique_id: Unique identifier for the agent.
            x, y: Agent initial location.
            agent_type: Indicator for the agent's type (minority=1, majority=0)
        '''
        super().__init__(pos, unique_id, model, agent_type, resources, affiliation, issuetree, policytree)
        self.pos = pos  # defines the position of the agent on the grid
        self.unique_id = unique_id  # unique_id of the agent used for algorithmic reasons
        self.agent_type = agent_type  # defines the type of agents from policymaker, policyentrepreneur and externalparty
        self.resources = resources  # resources used for agents to perform actions
        self.affiliation = affiliation  # political affiliation affecting agent interactions
        self.issuetree = issuetree  # issue tree of the agent (including partial issue of other agents)
        self.policytree = policytree # policy tree for future models
        self.members = members

        self.selected_PC = None; self.selected_S = None; self.selected_PI = None  # selected issues and policies

    def interactions_AS_intra_coalition(self):

        # todo - not changed yet

        """
        ACF+PL+Co (coalition version)
        This function is used to perform the different coalition interactions within the coalition itself during the
        agenda setting step.

        The interactions that can be performed are on the preferred states and on the causal beliefs.
        All of the actions are first graded based on conflict levels. Then the action that has the highest grade is
        selected. Finally, the action selected is implemented.
        """

        len_DC = self.model.len_DC; len_PC = self.model.len_PC; len_S = self.model.len_S
        action_number = len_DC + 1 # number of actions allowed in this step (causal beliefs, preferred states)

        # selection of the cw of interest
        cb_of_interest = []
        # consider only the causal relations related to the problem on the agenda
        for cb_choice in range(len_DC):
            cb_of_interest.append(len_DC + len_PC + len_S + self.selected_PC * len_PC + cb_choice)

        # assigning resources for the actions
        self.resources_action = self.resources

        #check coalition coherence
        ''' here check whether all agents within the coalition are within 0.2 of the coalition average '''

        coalition_coherence = True
        member_list = self.members
        random.shuffle(member_list)
        for agent_mem in member_list:
            coalition_goal = self.issuetree[self.model.number_activeagents][len_DC + self.selected_PC][1]
            agent_mem_goal = agent_mem.issuetree[agent_mem.unique_id][len_DC + self.selected_PC][1]
            print('Coalition:', coalition_goal, ', agent:', agent_mem_goal)
            if abs(coalition_goal - agent_mem_goal) > 0.1:
                print('No coherence')
                coalition_coherence = False

        # todo - incomplete below this line

        # making sure there are enough resources
        while self.resources_action > 0.001 or coalition_coherence == False:

            total_grade_list = [] # initialising the grade list
            total_agent_list = [] # initialising the agent list

            for target in self.model.schedule.agent_buffer(shuffled=True):  # going through the other agents
                if isinstance(target, ActiveAgent) and not isinstance(target, Coalition) \
                        and target != self:  # making sure it is an active agent and not a coalition and not self
                    total_agent_list.append(target.unique_id) # saving the agent considered (randomly selected)

                    # looking at causal beliefs
                    for i in range(len(cb_of_interest)): # go through all causal beliefs of interest
                        cb = cb_of_interest[i] # selecting the causal belief
                        value1 = self.issuetree[self.unique_id][cb][0]
                        value2 = target.issuetree[target.unique_id][cb][0]
                        conflict_level, diff = self.conflict_level_calc(value1, value2)
                        total_grade_list.append(conflict_level * abs(diff)/2)

                    # looking the preferred states (aka goal)
                    goal = len_DC + self.selected_PC # selecting the right goal
                    value1 = self.issuetree[self.unique_id][goal][1]
                    value2 = target.issuetree[target.unique_id][goal][1]
                    conflict_level, diff = self.conflict_level_calc(value1, value2) # calculating the conflict level
                    total_grade_list.append(conflict_level * diff)
            # print(total_agent_list)
            # print(total_grade_list)

            # selecting the best graded interaction
            max_best_action = max(total_grade_list)
            best_action_index = total_grade_list.index(max(total_grade_list)) # index of interaction in the list
            best_action_agent_id = total_agent_list[int(best_action_index/action_number)] # unique_id of interaction target
            # print(max_best_action, best_action_index, int(best_action_index/action_number), best_action_agent_id)

            best_action_type = best_action_index - action_number * int(best_action_index / action_number)
            # selecting the action type (0 is a causal belief action, 1 is a preferred state action)

            # performing the interaction
            for target in self.model.schedule.agent_buffer(shuffled=True):  # going through the other agents
                if target.unique_id == best_action_agent_id:  # making sure it is an active agent and not self
                    # print('Actor: #', self.unique_id, ', target: #', target.unique_id)
                    if best_action_type <= action_number - 1 - 1: # action type: causal belief
                        cb_choice = cb_of_interest[best_action_type]
                        target.issuetree[target.unique_id][cb_choice][0] += \
                        (self.issuetree[self.unique_id][cb_choice][0] -
                         target.issuetree[target.unique_id][cb_choice][0]) * (self.resources * 0.1)

                    if best_action_type == action_number - 1: # action type: preferred state
                        goal = len_DC + self.selected_PC
                        # print('Acting:', self.issuetree[self.unique_id][goal][1])
                        # print('Bf:', target.issuetree[target.unique_id][goal][1])
                        # print('Change', (self.issuetree[self.unique_id][goal][1] -
                        #      target.issuetree[target.unique_id][goal][1]) * (self.resources/100 * 0.1))
                        target.issuetree[target.unique_id][goal][1] += \
                            (self.issuetree[self.unique_id][goal][1] -
                             target.issuetree[target.unique_id][goal][1]) * (self.resources/100 * 0.1)
                        # print('Af:', target.issuetree[target.unique_id][goal][1])
                        # print(' ')

                    self.resources_action -= self.resources * 0.1 # removing the action resources

    def interactions_PF_intra_coalition(self):

        # todo - not changed yet

        """
        ACF+PL+Co (coalition version)
        This function is used to perform the different agent interactions for the active agents during the
        policy formulation step.

        The interactions that can be performed are on the preferred states and on the causal beliefs.
        All of the actions are first graded based on conflict levels. Then the action that has the highest grade is
        selected. Finally, the action selected is implemented.
        """

        len_DC = self.model.len_DC; len_PC = self.model.len_PC; len_S = self.model.len_S
        action_number = len_PC + 1 # number of actions allowed in this step (causal beliefs, preferred states)

        # selection of the cw of interest
        cb_of_interest = []
        # consider only the causal relations related to the problem on the agenda
        for cb_choice in range(len_PC):
            cb_of_interest.append(len_DC + len_PC + len_S + len_DC * len_PC + self.selected_S * len_S + cb_choice)
        # print(cb_of_interest)
        # print(' ')

        # assigning resources for the actions
        self.resources_action = self.resources

        # making sure there are enough resources
        while self.resources_action > 0.001:

            total_grade_list = [] # initialising the grade list
            total_agent_list = [] # initialising the agent list

            for target in self.model.schedule.agent_buffer(shuffled=True):  # going through the other agents
                if isinstance(target, ActiveAgent) and not isinstance(target, Coalition) \
                        and target != self:  # making sure it is an active agent and not a coalition and not self
                    total_agent_list.append(target.unique_id) # saving the agent considered (randomly selected)

                    agent_type_bonus = 1 # making sure policymakers are preferred for the PF interactions
                    if target.agent_type == 'policymaker':
                        agent_type_bonus = 1.1

                    # looking at causal beliefs
                    for i in range(len(cb_of_interest)): # go through all causal beliefs of interest
                        cb = cb_of_interest[i] # selecting the causal belief
                        value1 = self.issuetree[self.unique_id][cb][0]
                        value2 = target.issuetree[target.unique_id][cb][0]
                        conflict_level, diff = self.conflict_level_calc(value1, value2)
                        total_grade_list.append(conflict_level * abs(diff)/2 * agent_type_bonus)
                        # the abs is needed to take care of the causal belief range of [-1, 1]
                        # the /2 is used also due to a range twice as large as for the other interactions

                    # looking the preferred states (aka goal)
                    goal = len_DC + len_PC + self.selected_S # selecting the right goal
                    value1 = self.issuetree[self.unique_id][goal][1]
                    value2 = target.issuetree[target.unique_id][goal][1]
                    conflict_level, diff = self.conflict_level_calc(value1, value2) # calculating the conflict level
                    total_grade_list.append(conflict_level * diff * agent_type_bonus)
            # print(total_agent_list)
            # print(total_grade_list)

            # selecting the best graded interaction
            max_best_action = max(total_grade_list)
            best_action_index = total_grade_list.index(max(total_grade_list)) # index of interaction in the list
            best_action_agent_id = total_agent_list[int(best_action_index/action_number)] # unique_id of interaction target
            # print(max_best_action, best_action_index, int(best_action_index/action_number), best_action_agent_id)

            best_action_type = best_action_index - action_number * int(best_action_index / action_number)
            # selecting the action type (0 is a causal belief action, 1 is a preferred state action)

            # performing the interaction
            for target in self.model.schedule.agent_buffer(shuffled=True):  # going through the other agents
                if target.unique_id == best_action_agent_id:  # making sure it is an active agent and not self
                    # print('Actor: #', self.unique_id, ', target: #', target.unique_id)
                    if best_action_type <= action_number - 1 - 1: # action type: causal belief
                        cb_choice = cb_of_interest[best_action_type]
                        target.issuetree[target.unique_id][cb_choice][0] += \
                        (self.issuetree[self.unique_id][cb_choice][0] -
                         target.issuetree[target.unique_id][cb_choice][0]) * (self.resources * 0.1)

                    if best_action_type == action_number - 1: # action type: preferred state
                        goal = len_DC + len_PC + self.selected_S
                        # print('Aff.', self.affiliation)
                        # print('Acting:', self.issuetree[self.unique_id][goal][1])
                        # print('Bf:', target.issuetree[target.unique_id][goal][1])
                        # print('Change', (self.issuetree[self.unique_id][goal][1] -
                        #      target.issuetree[target.unique_id][goal][1]) * (self.resources/100 * 0.1))
                        target.issuetree[target.unique_id][goal][1] += \
                            (self.issuetree[self.unique_id][goal][1] -
                             target.issuetree[target.unique_id][goal][1]) * (self.resources/100 * 0.1)
                        # print('Af:', target.issuetree[target.unique_id][goal][1])
                        # print(' ')

                    self.resources_action -= self.resources * 0.1 # removing the action resources

    def interactions_AS_inter_coalition(self):

        # todo - not changed yet

        """
        ACF+PL+Co (coalition version)
        This function is used to perform the different agent interactions for the active agents during the
        agenda setting step.

        The interactions that can be performed are on the preferred states and on the causal beliefs.
        All of the actions are first graded based on conflict levels. Then the action that has the highest grade is
        selected. Finally, the action selected is implemented.
        """

        len_DC = self.model.len_DC; len_PC = self.model.len_PC; len_S = self.model.len_S
        action_number = len_DC + 1 # number of actions allowed in this step (causal beliefs, preferred states)

        # selection of the cw of interest
        cb_of_interest = []
        # consider only the causal relations related to the problem on the agenda
        for cb_choice in range(len_DC):
            cb_of_interest.append(len_DC + len_PC + len_S + self.selected_PC * len_PC + cb_choice)

        # assigning resources for the actions
        self.resources_action = self.resources

        # making sure there are enough resources
        while self.resources_action > 0.001:

            total_grade_list = [] # initialising the grade list
            total_agent_list = [] # initialising the agent list

            for target in self.model.schedule.agent_buffer(shuffled=True):  # going through the other agents
                if isinstance(target, ActiveAgent) and not isinstance(target, Coalition) \
                        and target != self:  # making sure it is an active agent and not a coalition and not self
                    total_agent_list.append(target.unique_id) # saving the agent considered (randomly selected)

                    # looking at causal beliefs
                    for i in range(len(cb_of_interest)): # go through all causal beliefs of interest
                        cb = cb_of_interest[i] # selecting the causal belief
                        value1 = self.issuetree[self.unique_id][cb][0]
                        value2 = target.issuetree[target.unique_id][cb][0]
                        conflict_level, diff = self.conflict_level_calc(value1, value2)
                        total_grade_list.append(conflict_level * abs(diff)/2)

                    # looking the preferred states (aka goal)
                    goal = len_DC + self.selected_PC # selecting the right goal
                    value1 = self.issuetree[self.unique_id][goal][1]
                    value2 = target.issuetree[target.unique_id][goal][1]
                    conflict_level, diff = self.conflict_level_calc(value1, value2) # calculating the conflict level
                    total_grade_list.append(conflict_level * diff)
            # print(total_agent_list)
            # print(total_grade_list)

            # selecting the best graded interaction
            max_best_action = max(total_grade_list)
            best_action_index = total_grade_list.index(max(total_grade_list)) # index of interaction in the list
            best_action_agent_id = total_agent_list[int(best_action_index/action_number)] # unique_id of interaction target
            # print(max_best_action, best_action_index, int(best_action_index/action_number), best_action_agent_id)

            best_action_type = best_action_index - action_number * int(best_action_index / action_number)
            # selecting the action type (0 is a causal belief action, 1 is a preferred state action)

            # performing the interaction
            for target in self.model.schedule.agent_buffer(shuffled=True):  # going through the other agents
                if target.unique_id == best_action_agent_id:  # making sure it is an active agent and not self
                    # print('Actor: #', self.unique_id, ', target: #', target.unique_id)
                    if best_action_type <= action_number - 1 - 1: # action type: causal belief
                        cb_choice = cb_of_interest[best_action_type]
                        target.issuetree[target.unique_id][cb_choice][0] += \
                        (self.issuetree[self.unique_id][cb_choice][0] -
                         target.issuetree[target.unique_id][cb_choice][0]) * (self.resources * 0.1)

                    if best_action_type == action_number - 1: # action type: preferred state
                        goal = len_DC + self.selected_PC
                        # print('Acting:', self.issuetree[self.unique_id][goal][1])
                        # print('Bf:', target.issuetree[target.unique_id][goal][1])
                        # print('Change', (self.issuetree[self.unique_id][goal][1] -
                        #      target.issuetree[target.unique_id][goal][1]) * (self.resources/100 * 0.1))
                        target.issuetree[target.unique_id][goal][1] += \
                            (self.issuetree[self.unique_id][goal][1] -
                             target.issuetree[target.unique_id][goal][1]) * (self.resources/100 * 0.1)
                        # print('Af:', target.issuetree[target.unique_id][goal][1])
                        # print(' ')

                    self.resources_action -= self.resources * 0.1 # removing the action resources

    def interactions_PF_inter_coalition(self):

        # todo - not changed yet

        """
        ACF+PL+Co (coalition version)
        This function is used to perform the different agent interactions for the active agents during the
        policy formulation step.

        The interactions that can be performed are on the preferred states and on the causal beliefs.
        All of the actions are first graded based on conflict levels. Then the action that has the highest grade is
        selected. Finally, the action selected is implemented.
        """

        len_DC = self.model.len_DC; len_PC = self.model.len_PC; len_S = self.model.len_S
        action_number = len_PC + 1 # number of actions allowed in this step (causal beliefs, preferred states)

        # selection of the cw of interest
        cb_of_interest = []
        # consider only the causal relations related to the problem on the agenda
        for cb_choice in range(len_PC):
            cb_of_interest.append(len_DC + len_PC + len_S + len_DC * len_PC + self.selected_S * len_S + cb_choice)
        # print(cb_of_interest)
        # print(' ')

        # assigning resources for the actions
        self.resources_action = self.resources

        # making sure there are enough resources
        while self.resources_action > 0.001:

            total_grade_list = [] # initialising the grade list
            total_agent_list = [] # initialising the agent list

            for target in self.model.schedule.agent_buffer(shuffled=True):  # going through the other agents
                if isinstance(target, ActiveAgent) and not isinstance(target, Coalition) \
                        and target != self:  # making sure it is an active agent and not a coalition and not self
                    total_agent_list.append(target.unique_id) # saving the agent considered (randomly selected)

                    agent_type_bonus = 1 # making sure policymakers are preferred for the PF interactions
                    if target.agent_type == 'policymaker':
                        agent_type_bonus = 1.1

                    # looking at causal beliefs
                    for i in range(len(cb_of_interest)): # go through all causal beliefs of interest
                        cb = cb_of_interest[i] # selecting the causal belief
                        value1 = self.issuetree[self.unique_id][cb][0]
                        value2 = target.issuetree[target.unique_id][cb][0]
                        conflict_level, diff = self.conflict_level_calc(value1, value2)
                        total_grade_list.append(conflict_level * abs(diff)/2 * agent_type_bonus)
                        # the abs is needed to take care of the causal belief range of [-1, 1]
                        # the /2 is used also due to a range twice as large as for the other interactions

                    # looking the preferred states (aka goal)
                    goal = len_DC + len_PC + self.selected_S # selecting the right goal
                    value1 = self.issuetree[self.unique_id][goal][1]
                    value2 = target.issuetree[target.unique_id][goal][1]
                    conflict_level, diff = self.conflict_level_calc(value1, value2) # calculating the conflict level
                    total_grade_list.append(conflict_level * diff * agent_type_bonus)
            # print(total_agent_list)
            # print(total_grade_list)

            # selecting the best graded interaction
            max_best_action = max(total_grade_list)
            best_action_index = total_grade_list.index(max(total_grade_list)) # index of interaction in the list
            best_action_agent_id = total_agent_list[int(best_action_index/action_number)] # unique_id of interaction target
            # print(max_best_action, best_action_index, int(best_action_index/action_number), best_action_agent_id)

            best_action_type = best_action_index - action_number * int(best_action_index / action_number)
            # selecting the action type (0 is a causal belief action, 1 is a preferred state action)

            # performing the interaction
            for target in self.model.schedule.agent_buffer(shuffled=True):  # going through the other agents
                if target.unique_id == best_action_agent_id:  # making sure it is an active agent and not self
                    # print('Actor: #', self.unique_id, ', target: #', target.unique_id)
                    if best_action_type <= action_number - 1 - 1: # action type: causal belief
                        cb_choice = cb_of_interest[best_action_type]
                        target.issuetree[target.unique_id][cb_choice][0] += \
                        (self.issuetree[self.unique_id][cb_choice][0] -
                         target.issuetree[target.unique_id][cb_choice][0]) * (self.resources * 0.1)

                    if best_action_type == action_number - 1: # action type: preferred state
                        goal = len_DC + len_PC + self.selected_S
                        # print('Aff.', self.affiliation)
                        # print('Acting:', self.issuetree[self.unique_id][goal][1])
                        # print('Bf:', target.issuetree[target.unique_id][goal][1])
                        # print('Change', (self.issuetree[self.unique_id][goal][1] -
                        #      target.issuetree[target.unique_id][goal][1]) * (self.resources/100 * 0.1))
                        target.issuetree[target.unique_id][goal][1] += \
                            (self.issuetree[self.unique_id][goal][1] -
                             target.issuetree[target.unique_id][goal][1]) * (self.resources/100 * 0.1)
                        # print('Af:', target.issuetree[target.unique_id][goal][1])
                        # print(' ')

                    self.resources_action -= self.resources * 0.1 # removing the action resources


class ElectorateAgent(Agent):
    '''
    Electorate agents.
    '''
    def __init__(self, pos, unique_id, model, affiliation, issuetree_elec, representativeness):
        '''
         Create a new Electorate agent.
         Args:
            unique_id: Unique identifier for the agent.
            x, y: Agent initial location.
            unique_id: 
        '''
        super().__init__(pos, model)
        self.pos = pos  # defines the position of the agent on the grid
        self.unique_id = unique_id  # unique_id of the agent used for algorithmic reasons
        self.affiliation = affiliation  # political affiliation affecting agent interactions
        self.issuetree_elec = issuetree_elec  # issue tree of the agent (including partial issue of other agents)
        self.representativeness = representativeness


    def electorate_influence(self, w_el_influence):

        '''
        This function is used to perform the electorate influence on the policy makers.
        This function is dependent on the electorate influence weight value which can be adjusted as a tuning parameter.
        '''

        len_DC = self.model.len_DC; len_PC = self.model.len_PC; len_S = self.model.len_S

        for agent in self.model.schedule.agent_buffer(shuffled=True):
            if isinstance(agent, ActiveAgent) and agent.agent_type == 'policymaker' \
                    and agent.affiliation == self.affiliation:
                # print(' ')
                # print('Before', agent.issuetree[agent.unique_id])
                _unique_id = agent.unique_id
                for issue in range(len_DC + len_PC + len_S):
                    agent.issuetree[_unique_id][issue][1] += \
                        (self.issuetree_elec[issue] - agent.issuetree[_unique_id][issue][1]) * w_el_influence

class TruthAgent(Agent):
    '''
    Truth agents.
    '''
    def __init__(self, pos, model, issuetree_truth, policytree_truth):
        '''
         Create a new Truth agent.
         Args:
            unique_id: Unique identifier for the agent.
            x, y: Agent initial location.
        '''
        super().__init__(pos, model)
        self.pos = pos  # defines the position of the agent on the grid
        self.issuetree_truth = issuetree_truth  # issue tree of the agent (including partial issue of other agents)
        self.policytree_truth = policytree_truth
