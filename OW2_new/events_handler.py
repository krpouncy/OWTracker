import os

import pandas as pd
from flask import jsonify

from models import EventsHandlerInterface
from app.core.state import app_state

class UserEventsHandler(EventsHandlerInterface):
    def __init__(self):
        print("Initializing Custom Events Handler")

        # Preprocess and unify symmetrical rules
        rules_df = pd.read_csv("models/OW2_new/team_rules.csv")
        self.preprocessed_rules_df = self.preprocess_rules_at_startup(rules_df)

    def handle_event(self, socket_object, event_name, payload = None):
        """Handle the given event with the given payload."""
        print(f"Handling event {event_name} with payload: {payload}")

        # 'page_load' event is called when the current HTML page is loaded
        if event_name == 'page_load':
            # use the preprocessed rules to send the rules to the client
            payload = self.preprocessed_rules_df.to_dict(orient='records')
            socket_object.emit("update_hidden_rules_div", payload)

        #  This event is called after 'get_stats_and_details' and 'predict_probability' methods return the output
        #  The call source is the 'process_screenshot' method in 'game_manager.py'
        if event_name == "game_details":
            # calculate the team_status and update the player status
            stats, game_details = payload
            time, team_composition, win_probability = game_details

            team_status = self.calculate_team_statuses(stats)
            self.update_player_status(socket_object, team_status, team_composition)

            socket_object.emit('team_rules', self.get_rules_table(team_composition, team_status, win_probability))

        # This event is called when the game outcome is set by the user in the browser
        # The call source is the 'set_game_outcome' method in 'routes.py'
        if event_name == 'game_outcome_set':
            # reset the chart
            socket_object.emit('reset_chart')

        # This event is called directly after the implemented 'predict_probability' method. It returns the output
        # The call source is the 'predict_probability' method in 'game_manager.py'
        # The 'predict_probability' method is created by the user in the 'predictor.py' file
        if event_name == 'game_prediction':
            # This event is called when an output is received from user implemented 'predict_probability' method
            # update the chart with the new probability
            socket_object.emit('update_chart', payload)

        print("Event handled.")

    def update_player_status(self, socket_object, team_status, team_composition):
        """Update the player status based on the given team status and composition."""
        # remove the label_ prefix from each person in the team
        team_players = ['_'.join(player.split('_')[1:]) for player in team_composition]
        print(team_players)

        tank_status, dps_status, support_status = team_status

        socket_object.emit('performance_update', {
            'tank': {'status': tank_status, 'text': 'Tank: ' + tank_status},
            'damage': {'status': dps_status, 'text': 'Damage: ' + dps_status},
            'support': {'status': support_status, 'text': 'Support: ' + support_status},
            'team_composition': team_players
        })

    def calculate_team_statuses(self, stats):
        """Calculate the status of the tank, dps, and support roles based on the given stats.

        :param stats: A list of 5 lists (representing players on Team) with each containing 6 numeric values for K, A, D, Dmg, H, and MIT.
        :return: A tuple of strings representing the status of the tank, dps, and support roles.
        """
        # initialize the status of each role
        tank_status, dps_status, support_status = 'not enough data', 'not enough data', 'not enough data'

        # calculate the tank, dps, and support status
        tank_k, tank_mit = stats[0][0], stats[0][5]
        if tank_k != 0 and tank_mit != 0:
            tank_ratio = tank_k / (tank_k + tank_mit ** 0.5)
            if tank_ratio <= 0.05:
                tank_status = 'poor'
            elif 0.04 < tank_ratio < 0.08:
                tank_status = 'average'
            else:
                tank_status = 'good'

        dps_damage = stats[1][3] + stats[2][3]
        enemy_dps_damage = stats[6][3] + stats[7][3]
        if dps_damage != 0 and enemy_dps_damage != 0:
            if abs(dps_damage - enemy_dps_damage) < 274:
                dps_status = 'average'
            elif dps_damage - enemy_dps_damage >= 274:
                dps_status = 'good'
            else:
                dps_status = 'poor'

        damage = stats[3][3] + stats[4][3]
        healing = stats[3][4] + stats[4][4]
        if damage != 0 and healing != 0:
            if damage + healing > 0:
                damage_ratio = damage / (damage + healing)
            else:
                damage_ratio = 0.0

            print(f"Damage Ratio: {damage_ratio:.2f}. Feedback: ", end="")

            if damage_ratio < 0.14:
                print("SHOOT!")
                support_status = 'poor'
            elif 0.185 <= damage_ratio <= 0.32:
                print("You're doing good.")
                support_status = 'average'
            else:
                support_status = 'good'

        print("Custom Team Status:", (tank_status, dps_status, support_status))

        return tank_status, dps_status, support_status

    # preprocess the rules
    def create_rule_str(self, left_str, right_str):
        left_str = left_str.strip("{}")
        right_str = right_str.strip("{}")
        items = [x.strip() for x in left_str.split(",") if x.strip()]
        items += [x.strip() for x in right_str.split(",") if x.strip()]
        items.sort()
        return items

    def preprocess_rules_at_startup(self, df):
        """
        Combine the rules into single list and remove duplicates
        """
        # Create new columns for normalized LHS / RHS
        df["combined"] = df.apply(lambda x: self.create_rule_str(x["lhs"], x["rhs"]), axis=1)

        # remove duplicate combined
        df.drop_duplicates(subset=["combined"], inplace=True)

        def tuple_to_str(ls_):
            # Rebuild as { item1, item2, ... }
            if len(ls_) == 0:
                return "{}"
            return "{" + ", ".join(ls_) + "}"

        df["combined"] = df["combined"].apply(lambda x: tuple_to_str(x))
        return df

    def get_filtered_rules(self, tank_status, dps_status, support_status, outcome):
        """ Filters the preprocessed df rules based on the given statuses and outcome prediction """
        if tank_status == 'not enough data' or dps_status == 'not enough data' or support_status == 'not enough data':
            required = {f"RESULT=1"}
        else:
            required = {f"TANK={tank_status}", f"DPS={dps_status}", f"SUP={support_status}", f"RESULT={outcome}"}

        def lhs_contains_all_items(lhs_str):
            # e.g. LHS = "{TANK=good, CHAR_1_DPS=Ashe, YOU=Moira}"
            lhs_clean = lhs_str.strip("{}")
            items = [x.strip() for x in lhs_clean.split(",") if x.strip()]
            return required.issubset(items)

        filtered = self.preprocessed_rules_df[
            self.preprocessed_rules_df["combined"].apply(lhs_contains_all_items)
        ].copy()

        return filtered

    def get_rules_table(self, team_composition, team_statuses, win_probability):
        tank_status, dps_status, support_status = team_statuses
        if tank_status == 'not enough data' or dps_status == 'not enough data' or support_status == 'not enough data':
            win_probability = 1
        else:
            win_probability = 1 if win_probability > 0.5 else 0

        # remove the prefix from members in team composition
        team_composition = ['_'.join(player.split('_')[1:]) for player in team_composition] #TODO could be an issue in the future

        # get filtered rules and sort by lift desc
        filtered = self.get_filtered_rules(tank_status=tank_status,
                                      dps_status=dps_status,
                                      support_status=support_status,
                                      outcome=win_probability)

        if filtered.empty:
            # return jsonify({"table_html": "<p>No rules found for these statuses</p>"})
            return {"table_html": "<p>No rules found for these statuses</p>"}

        # Hide TANK=, DPS=, SUP=, and RESULT= from display
        def remove_statuses(_str):
            items = _str.strip("{}").split(",")
            cleaned = []
            for it in items:
                it = it.strip()
                if it.startswith("TANK=") or it.startswith("DPS=") or it.startswith("SUP=") or it.startswith("RESULT="):
                    continue
                else:
                    it = it.split("=")[1]
                cleaned.append(it)
            if len(cleaned) == 0:
                return "{}"
            return ", ".join(cleaned)

        # iter, remove status and save to new column
        filtered.loc[:, "combined"] = filtered["combined"].apply(remove_statuses)

        # # create a new column that counts the number of members in current_comp that exist in team_composition
        filtered.loc[:, "num_exist"] = filtered["combined"].apply(
            lambda x: len([member for member in x.split(", ") if member in team_composition]))

        # sort by num_exist descending
        sorted_filtered = filtered.sort_values(by=["num_exist", "lift"], ascending=False)

        # remove rows that have 0 for num_exist
        sorted_filtered = sorted_filtered[sorted_filtered["num_exist"] > 0]

        max_exist = sorted_filtered["num_exist"].max()
        rows = []
        for _, row in sorted_filtered.iterrows():
            class_option = ""
            if max_exist > 1:
                class_option = "table-primary" if row['num_exist'] == max_exist else ""

            rows.append(f"""
                    <tr class="{class_option}">
                        <td class="text-start">{row['combined']}</td>
                    </tr>
                    """)

        table_header = "Winning Comps" if int(win_probability) == 1 else "Losing Comps"
        table_header += f" ({max_exist} player match)"

        table_html = f"""
        <table class="table table-hover theme-table">
            <thead>
                <tr>
                    <th class="theme-table-header text-center">{table_header}</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """

        # return jsonify({"table_html": table_html, "rules": sorted_filtered.to_dict(orient='records')})
        return {"table_html": table_html, "rules": sorted_filtered.to_dict(orient="records")}
