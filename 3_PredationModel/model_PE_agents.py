from mesa import Agent
import copy

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

        # compiling all the preferences
        PC_pref_list = [None for k in range(self.model.len_PC)]
        for i in range(self.model.len_PC):
            PC_pref_list[i] = self.issuetree[self.unique_id][self.model.len_DC + i][2]


        self.selected_PC = PC_pref_list.index(max(PC_pref_list))  # assigning the highest preference

    def selection_S(self):

        '''
        This function is used to select the preferred secondary issue. First, only the secondary issues that are
        related, through a causal relation, to the policy core issue on the agenda are placed into an array. Then,
        the one with the highest preference is selected. It is then used as the issue that the agent will advocate for
        later on.
        '''

        len_DC = self.model.len_DC; len_PC = self.model.len_PC; len_S = self.model.len_S

        # considering only issues related to the issue on the agenda
        S_pref_list_indices = []
        for i in range(len_S):
            cr = len_DC + len_PC + len_S + len_DC * len_PC + self.model.agenda_PC * len_S + i
            if self.issuetree[self.unique_id][cr][0] != 0:
                S_pref_list_indices.append(i)

        S_pref_list = [None for i in range(len(S_pref_list_indices))]
        for i in range(len(S_pref_list)):
            S_pref_list[i] = self.issuetree[self.unique_id][len_DC + len_PC + S_pref_list_indices[i]][2]

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

        # selecting the policy instrument from the policy family on the agenda
        PFIns_indices = copy.copy(self.model.PF_indices[self.model.agenda_PF])
        len_PFIns_indices = len(PFIns_indices)

        '''making sure not to include non-agenda related policies'''
        # finding a secondary issue not related to the agenda
        S_list_indices = []
        for i in range(len_S):
            cr = len_DC + len_PC + len_S + len_DC * len_PC + self.model.agenda_PC * len_S + i
            if -0.01 >= self.issuetree[self.unique_id][cr][0] >= 0.01:
            # if self.issuetree[self.unique_id][cr][0] >= -0.01 and self.issuetree[self.unique_id][cr][0] <= 0.01:
                S_list_indices.append(i)

        # finding a policy instrument only affecting the secondary issues selected above
        for PIj in range(len(PFIns_indices)): # going through all instruments
            i = 0 # starting counter for while loop
            inst_check = [] # make a list of all interaction between the instrument and the concerned secondary issues
            while i < len(S_list_indices): # checking the indices recorded

                Si = S_list_indices[i] # selecting the secondary issue
                inst_check.append(abs(self.policytree[self.unique_id][len_PF + PIj][Si])) # recording the impacts
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
                state = self.issuetree[self.unique_id][len_DC + len_PC + Si][0]
                goal = self.issuetree[self.unique_id][len_DC + len_PC + Si][1]
                impact = self.policytree[self.unique_id][len_PF + PIj][Si]

                new_state = (state * (1 + impact))  # calculation of the impact of the instrument on the state
                gap = abs(goal - new_state)  # calculation of the goal-state gap

                PI_denominator += round(gap,3) # adding up to the denominator

        # numerator
        for PIj in PFIns_indices: # going through all policy instruments

            PI_numerator = 0 # resetting the numerator counter for each policy instrument
            for Si in range(len_S): # going through all secondary issues
                state = self.issuetree[self.unique_id][len_DC + len_PC + Si][0]
                goal = self.issuetree[self.unique_id][len_DC + len_PC + Si][1]
                impact = self.policytree[self.unique_id][len_PF + PIj][Si]

                new_state = (state * (1 + impact)) # calculation of the impact of the instrument on the state
                gap = abs(goal - new_state) # calculation of the goal-state gap

                PI_numerator += round(gap, 3) # adding up to the numerator (per policy instrument)

            self.policytree[self.unique_id][len_PF + PIj][len_S] = \
                round(PI_numerator/PI_denominator,3) # assigning the preference value (per policy instrument)

        '''selection of the preferred policy instrument'''
        # compiling all the preferences
        PI_pref_list = [1 for k in range(len_PFIns_indices)] # we use 1 as the lowest gap is selected later
        for PIj in PFIns_indices:
            PI_pref_list[PIj] = self.policytree[self.unique_id][len_PF + PIj][len_S]

        # assigning the lowest preference as the selected policy instrument by the agent
        # lowest gap is preferred for agents - hence lowest preference
        self.selected_PI = PI_pref_list.index(min(PI_pref_list))
        self.selected_PI = self.model.PF_indices[self.model.agenda_PF][self.selected_PI]

    def interactions_AS_PL(self):

        # todo - missing the agent interactions here (for the agenda setting)

        """
        ACF+PL
        This function is used to perform the different agent interactions for the active agents during the
        agenda setting step.

        The interactions that can be performed are on the preferred states and on the causal beliefs.
        All of the actions are first graded based on conflict levels. Then the action that has the highest grade is
        selected. Finally, the action selected is implemented.

        Note the agent strategy of performing the same action as long as the conflict level is not low and that the
        agent still has resources.

        """

        # saving the conflict level numbers


        DC_inclusion = True # todo - change this

        len_DC = self.model.len_DC; len_PC = self.model.len_PC; len_S = self.model.len_S
        total_issue_number = len_DC + len_PC + len_S

        # todo - need the addition of a check that the DC are considered - if not,
        #  then the causal relations should not be considered either
        # selection of the cw of interest
        if DC_inclusion == True:
            cb_of_interest = []
            # consider only the causal relations related to the problem on the agenda
            for cb_choice in range(len_PC):
                cb_of_interest.append(len_DC + len_PC + len_S + self.selected_PC * len_PC + cb_choice)
            print(cb_of_interest)

        # making sure there are enough resources
        while self.resources > 0.001:

            total_grade_list = [] # initialising the grade list
            total_agent_list = [] # initialising the agent list

            print(self.unique_id, '/n')
            for target in self.model.schedule.agent_buffer(shuffled=True):  # going through the other agents
                if isinstance(target, ActiveAgent) and target != self:  # making sure it is an active agent and not self

                    # saving the agent considered (randomly selected)
                    total_agent_list.append(target.unique_id)

                    # looking at causal beliefs
                    if DC_inclusion == True: # in case the model has deep core issues

                        for i in range(len(cb_of_interest)): # go through all causal beliefs of interest
                            cb = cb_of_interest[i] # selecting the causal belief
                            value1 = self.issuetree[self.unique_id][cb][0]
                            value2 = target.issuetree[target.unique_id][cb][0]
                            conflict_level = self.conflict_level_calc(value1, value2)
                            total_grade_list.append(conflict_level)

                    else: # if the deep core issues are not considered
                        for i in range(len_PC):
                            conflict_level = 0 # nul value so that causal beliefs are not considered
                            total_grade_list.append(conflict_level)

                    # looking the preferred states (aka goal)
                    print('self.selected_PC', self.selected_PC)
                    goal = len_DC + self.selected_PC # selecting the right goal
                    value1 = self.issuetree[self.unique_id][goal][1]
                    value2 = target.issuetree[target.unique_id][goal][1]
                    print(value1, value2)
                    conflict_level = self.conflict_level_calc(value1, value2) # calculating the conflict level
                    total_grade_list.append(conflict_level)

            # todo - the current approach makes it a delicate task to have interaction between agents - this threshold
            #  approach - there might be a need to find something else.


            print(target.unique_id)
            print(total_grade_list)
            print(total_agent_list)

            # creation of the grades
            # selection of the action
            # performing the action
            # if resources are not exhausted:
            #   check conflict level on that belief
            #   if still not low, perform action and repeat until resources are exhausted or conflict level is now low
            #   if conflict level not low, start from the beginning again

            # Going through all the links in the model
            # print(agents)
            total_grade_list = []
            total_grade_list_links = []



            for links in link_list:

                # Making sure that the link is attached to the agent and has a aware higher than 0
                if (links.agent1 == agents or links.agent2 == agents) and links.aware > 0:
                    total_grade_list_links.append(links)

                    # 1. Grading all framing actions:
                    # Checking through all possible framing - This is all based on partial knowledge!
                    for cw in cw_of_interest:
                        cw_grade = ActionFunctions.action_grade_calculator(links, cw, 0, agents, affiliation_weights)
                        total_grade_list.append(cw_grade)

                    # 2. Grading all individual actions - Aim change
                    aim_grade = ActionFunctions.action_grade_calculator(links, agents.select_as_issue, 1, agents,
                                                                        affiliation_weights)
                    total_grade_list.append(aim_grade)

                    # 3. Grading all individual actions - State change
                    state_grade = ActionFunctions.action_grade_calculator(links, agents.select_as_issue, 0, agents,
                                                                          affiliation_weights)
                    total_grade_list.append(state_grade)

            # print(' ')
            # print('Number of actions: ' + str(len(total_grade_list)))
            # print(total_grade_list)

            # 4. Choosing an action
            # Check if several actions have the same grade
            min_best_action = min(total_grade_list)
            count_min_list = []
            count = 0
            for item in total_grade_list:
                if item == min_best_action:
                    count_min_list.append(count)
                count += 1
            # print('List of indexes: ' + str(count_min_list))
            # print(' ')

            # If there are several grades at the same level, then choose a random action from these grades:
            if len(count_min_list) > 1:
                best_action_index = random.choice(count_min_list)
            # print('Randomly chosen best action: ' + str(best_action_index))
            else:
                best_action_index = total_grade_list.index(min(total_grade_list))
            # print('Not randomly chosen: ' + str(best_action_index))

            # print(' ')
            # print('----- New check for best action ------')
            # print('Action value: ' + str(min(total_grade_list)))
            # print('Index of the best action: ' + str(best_action_index))
            # print('This is the grade of the action: ' + str(total_grade_list[best_action_index]))
            # Make sure that we do not take into account the 0 from the list to perform the following calculations
            # best_action_index += 1
            # print('The total amount of links considered: ' + str(len(total_grade_list_links)))
            # print('The number of actions per link considered: ' + str(len(cw_of_interest) + 2))
            # print('The total amount of actions considered: ' + str(len(total_grade_list)))
            # print('The link for the action is: ' + str(int(best_action_index/(len(cw_of_interest) + 2))))
            best_action = best_action_index - (len(cw_of_interest) + 2) * int(
                best_action_index / (len(cw_of_interest) + 2))
            # print('The impacted index is: ' + str(best_action))
            # print('The would be index without the +1: ' + str((best_action_index - (len(cw_of_interest) + 2)
            # * int(best_action_index/(len(cw_of_interest) + 2))) - 1))
            # print('   ')

            # 5. Performing the actual action
            # Selecting the link:
            for links in link_list:

                if links == total_grade_list_links[int(best_action_index / (len(cw_of_interest) + 2))]:
                    # print(links)

                    # Update of the aware decay parameter
                    links.aware_decay = 5

                    # If the index is in the first part of the list, then the framing action is the best
                    if best_action <= len(cw_of_interest) - 1:
                        # print(' ')
                        # print('Framing action - causal relation')
                        # print('best_action: ' + str(best_action))
                        # print('cw_of_interest: ' + str(cw_of_interest))
                        # print('cw_of_interest[best_action]: ' + str(cw_of_interest[best_action]))

                        implemented_action = ActionFunctions.action_implementor(links, cw_of_interest[best_action], 0,
                                                                                agents, agents, affiliation_weights,
                                                                                resources_weight_action,
                                                                                resources_potency, False, 1)

                    # If the index is in the second part of the list, then the aim influence action is the best
                    if best_action == len(cw_of_interest):
                        # print('Implementing a aim influence action:')

                        implemented_action = ActionFunctions.action_implementor(links, agents.select_as_issue, 1,
                                                                                agents, agents, affiliation_weights,
                                                                                resources_weight_action,
                                                                                resources_potency, False, 1)

                    # If the index is in the first part of the list, then the state influence action is the best
                    if best_action == len(cw_of_interest) + 1:
                        # print('Implementing a state influence action:')

                        implemented_action = ActionFunctions.action_implementor(links, agents.select_as_issue, 0,
                                                                                agents, agents, affiliation_weights,
                                                                                resources_weight_action,
                                                                                resources_potency, False, 1)

            # agents.resources_actions -= agents.resources
            agents.resources_actions -= agents.resources[0] * resources_weight_action

        return 0

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

        return conflict_level

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
