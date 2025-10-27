from bs4 import BeautifulSoup
import requests
import csv
import math
import pandas as pd
import os

# CMU ATHLETICS WEB WEBPAGE: https://athletics.cmu.edu/sports/wbkb/index

# TODO: copy and paste the url for roster/ schedule of the desired season on the roster/ schedule tab of the CMU Athletics WBB Webpage
roster_url = input("Enter the roster URL from the CMU Athletics WebPage for your desired season: ")
schedule = input("Enter the schedule URL from the CMU Athletics WebPage for your desired season: ")
#roster_url = "https://athletics.cmu.edu/sports/mbkb/2024-25/roster"
#schedule = "https://athletics.cmu.edu/sports/mbkb/2024-25/schedule"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                   (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

s = requests.get(schedule, headers=headers)
soup_schedule = BeautifulSoup(s.text, "html.parser")

title = soup_schedule.find("div", class_="page-content schedule-content enhanced")
season = title.find("h1").get_text().split(" ")[0].replace("-","_")
links = soup_schedule.find_all("a")

opponent_list = []
boxScore_list = []
play_list = []
for link in links:
    if link.get_text() is not None and "Box Score" in link.get_text():
        info = link["aria-label"]
        game = info.split(":")[3]
        if " at " in game:
            other_team = game.split("at")[1].strip()
            if "#" in other_team:
                opponent_split = other_team.lstrip("#").split(" ")
                opponent_team = ""
                for word in opponent_split[1:]:
                    opponent_team += word.lower() + " "
                if opponent_team.strip() in opponent_list:
                    opponent_list.append(opponent_team.strip() + "2")
                else:
                    opponent_list.append(opponent_team.strip())
            else:
                opponent_team = other_team.lower().strip()
                if opponent_team in opponent_list:
                    opponent_list.append(opponent_team + "2")
                else:
                    opponent_list.append(opponent_team)
        else:
            other_team = game.split("vs.")[0].strip()
            if "#" in other_team:
                opponent_split = other_team.lstrip("#").split(" ")
                opponent_team = ""
                for word in opponent_split[1:]:
                    opponent_team += word.lower() + " "
                if opponent_team.strip() in opponent_list:
                    opponent_list.append(opponent_team.strip() + "2")
                else:
                    opponent_list.append(opponent_team.strip())
            else:
                opponent_team = other_team.lower().strip()
                if opponent_team in opponent_list:
                    opponent_list.append(opponent_team + "2")
                else:
                    opponent_list.append(opponent_team)
        boxScore_list.append(f'http://athletics.cmu.edu{link["href"]}')

for bs in boxScore_list:
    play_by_play = requests.get(bs, headers=headers)
    soup_play_by_play = BeautifulSoup(play_by_play.text, "html.parser")
    all_links = soup_play_by_play.find_all("a")
    for li in all_links:
        if li.get_text() is not None and "Play by Play" in li.get_text():
            play_list.append(f'http://athletics.cmu.edu{li["href"]}')

games_dict = {}
for opp, box, play in zip(opponent_list, boxScore_list, play_list):
    games_dict[opp] = box, play

# TODO: comment these lines out if schedule does not have score inputted for exhibition game
games = soup_schedule.find_all("div", class_="event-opponent h5 align-middle m-0")
for div in games:
    opponent_name = div.find("span", class_= "event-opponent-name").get_text()
    if div.find("span", attrs={"title": "Do not count in overall record"}) is not None:
        if "#" in opponent_name:
            opponent_split = opponent_name.lstrip("#").split(" ")
            opponent_remove = ""
            for word in opponent_split[1:]:
                opponent_remove += word.lower() + " "
        else:
            opponent_remove = opponent_name
        del games_dict[opponent_remove.strip().lower()]

game_order = ""
for key, values in games_dict.items():
    opponent = key
    game_order += opponent + ","
    box_score = values[0]
    play_by_play = values[1]
    # scraping CMU roster data for that season from CMU Athletics WBB Webpage
    roster = requests.get(roster_url, headers=headers)
    soup_roster = BeautifulSoup(roster.text, "html.parser")

    # create dictionary mapping name to position
    positions_dict = {}
    position_list = []

    # making list of positions
    for positions in soup_roster.find_all("td", class_="text-nowrap"):
        # bc Pos is in span so looking for span of td with text "Pos.:"
        if positions.find("span") is not None and "Pos.:" in positions.find("span").get_text():
            pos_label = positions.get_text(separator=" ", strip=True)
            pos = pos_label.replace("Pos.:", "").strip()
            position_list.append(pos)

    # create dictionary mapping name to number
    numbers_dict = {}
    numbers_list = []

    # making list of numbers
    for numbers in soup_roster.find_all("td", class_="text-inherit jersey-number d-none d-md-table-cell"):
        if numbers.find("span") is not None and "No.:" in numbers.find("span").get_text():
            num_label = numbers.get_text(separator=" ", strip=True)
            num = num_label.replace("No.:", "").strip()
            numbers_list.append(num)

    # mapping name to number and name to position
    i = 0
    for names in soup_roster.find_all("th", class_="text-inherit"):
        name = names.get_text(separator=" ", strip=True)
        cleaned = ' '.join(name.split())
        capitalized = cleaned.upper().split(' ')
        positions_dict[capitalized[1] + "," + capitalized[0]] = position_list[i]
        numbers_dict[capitalized[1] + "," + capitalized[0]] = numbers_list[i]
        i += 1

    boxScore = requests.get(box_score, headers=headers)
    soup_boxScore = BeautifulSoup(boxScore.text, "html.parser")
    # if player quit mid-season and was removed from roster
    players = soup_boxScore.find_all("th", class_="row-head pinned-col text")
    for player in players:
        if player.find("a") is not None:
            full_name = ""
            name = player.find("a").get_text().split(" ")
            full_name = name[1].upper() + "," + name[0].upper()
            if full_name not in numbers_dict.keys():
                number = player.find("span", class_="uniform").get_text().rstrip(" -")
                position = player.find("span", class_="position").get_text().lstrip("- ").upper()
                numbers_dict[full_name] = number
                positions_dict[full_name] = position

    # scrape the starters who are listed first (aka first 5 player names)
    starters = soup_boxScore.find_all("a", class_="player-name")[0:5]

    # combine to identify starting lineup
    starting_lineup = ""
    for starter in starters:
        full_name = starter.text.upper().split(" ")
        starting_lineup += full_name[1] + "," + full_name[0] + ", "
    starting_lineup = starting_lineup.rstrip(", ")


    # function to count number of guards in a lineup
    def num_guards(lineup):
        num_g = 0
        position_lineup = lineup.split(", ")
        for position in position_lineup:
            if positions_dict[position] == 'G':
                num_g += 1
        return str(num_g)


    # function to get the numbers of the players in a lineup
    def number_players(lineup):
        numbers_str = ""
        player_lineup = lineup.split(", ")
        for player in player_lineup:
            numbers_str += numbers_dict[player] + " "
        return numbers_str.strip()


    # home or away team - if image of first visitor row of plays is CMU then CMU is visitor
    play_data = requests.get(play_by_play, headers=headers)
    soup_plays = BeautifulSoup(play_data.text, "html.parser")

    # Assigns variable "row" to all visitor team actions
    row = soup_plays.find_all("tr", class_="row visitor")

    # Scrapes visitor team logo
    img = row[0].find("img", class_="team-logo visitor")

    # If visitor logo is Carnegie Mellon, the Carnegie Mellon is the away team (and vice versa)
    if img and "Carnegie Mellon" in img.get("alt", ""):
        score1 = "v-score"
        score2 = "h-score"
        tag = "AWAY"
        cmu_score = soup_plays.find("div", class_="team-score visitor").get_text().strip()
        opponent_score = soup_plays.find("div", class_="team-score home").get_text().strip()
        cmu_actions = soup_plays.find_all("tr", class_=["row visitor", "row visitor score-changed"])
        opponent_actions = soup_plays.find_all("tr", class_=["row home", "row home score-changed"])
    else:
        score1 = "h-score"
        score2 = "v-score"
        tag = "HOME"
        cmu_score = soup_plays.find("div", class_="team-score home").get_text().strip()
        opponent_score = soup_plays.find("div", class_="team-score visitor").get_text().strip()
        cmu_actions = soup_plays.find_all("tr", class_=["row home", "row home score-changed"])
        opponent_actions = soup_plays.find_all("tr", class_=["row visitor", "row visitor score-changed"])

    # Scrape substitution data
    # Assigns "sub_out" to a list of players who exited the game and the time/ score differential at that time
    # Assigns "sub_in" to a list of players who entered the game and the time/ score differential at that time
    sub_out = []
    sub_in = []

    for row in cmu_actions:
        if "goes to the bench" in row.text:
            time = row.find("td", class_="time")
            out = row.find("span", class_="text")
            player_out = out.text.split("goes")
            c_score = row.find("span", class_=score1)
            o_score = row.find("span", class_=score2)
            score_diff = int(c_score.text) - int(o_score.text)
            sub_out.append([time.text, player_out[0].strip(), score_diff])
        elif "enters the game" in row.text:
            time = row.find("td", class_="time")
            into = row.find("span", class_="text")
            player_in = into.text.split("enters")
            v_score = row.find("span", class_="v-score")
            h_score = row.find("span", class_="h-score")
            score_diff = int(v_score.text) - int(h_score.text)
            sub_in.append([time.text, player_in[0].strip(), score_diff])


    # Assigns "total_o_pos" to a list of all the opponents possessions
    total_o_pos = []
    for o in opponent_actions:
        time = o.find("td", class_="time")
        play = o.find("span", class_="text")
        total_o_pos.append([time.get_text(strip=True), play.get_text(strip=True)])

    # Assigns "total_cmu_pos" to a list of all of cmu possessions
    total_cmu_pos = []
    for cmu in cmu_actions:
        time2 = cmu.find("td", class_="time")
        play2 = cmu.find("span", class_="text")
        total_cmu_pos.append([time2.get_text(strip=True), play2.get_text(strip=True)])

    q1_out = []
    q2_out = []
    q3_out = []
    q4_out = []
    ot_out = []
    q1_in = []
    q2_in = []
    q3_in = []
    q4_in = []
    ot_in = []

    # Function that splits sub outs and ins into quarters
    def quarter(quart, q, max_time, sub_list):
        for t, player, score in sub_list:
            if int(t.replace(":","")) <= max_time:
                max_time = int(t.replace(":",""))
                q.append([t, player, score, quart])
            else:
                break

        for t, player, score, quart in q:
            sub_list.remove([t, player, score])


    # Assigns q1_out to a list of players who exited the game in the first quarter
    # and the time/ score differential at that time of the quarter
    quarter(1, q1_out, 1000, sub_out)
    quarter(2, q2_out, 1000, sub_out)
    quarter(3, q3_out, 1000, sub_out)
    quarter(4, q4_out, 1000, sub_out)
    quarter('OT', ot_out, 1000, sub_out)
    quarter(1, q1_in, 1000, sub_in)
    quarter(2, q2_in, 1000, sub_in)
    quarter(3, q3_in, 1000, sub_in)
    quarter(4, q4_in, 1000, sub_in)
    quarter('OT', ot_in, 1000, sub_in)


    q1_o = []
    q2_o = []
    q3_o = []
    q4_o = []
    ot_o = []
    q1_cmu = []
    q2_cmu = []
    q3_cmu = []
    q4_cmu = []
    ot_cmu = []


    # Function that splits possessions into quarters
    def quarter_o(q, max_time, total_o):
        if total_o is not None:
            for tim, plays in total_o:
                if int(tim.replace(":","")) <= max_time:
                    max_time = int(tim.replace(":",""))
                    q.append([tim, plays])
                else:
                    for t, p in q:
                        total_o.remove([t, p])
                    return total_o
        else:
            return


    # Assigns q1_o to a list of all opponent possessions in the first quarter
    quarter_o(ot_o, 1000, quarter_o(q4_o, 1000, quarter_o(q3_o, 1000, quarter_o(q2_o, 1000, quarter_o(q1_o, 1000,
                                                                                                      total_o_pos)))))
    quarter_o(ot_cmu, 1000, quarter_o(q4_cmu, 1000, quarter_o(q3_cmu, 1000, quarter_o(q2_cmu, 1000, quarter_o(
        q1_cmu, 1000, total_cmu_pos)))))


    # Function that counts number of possessions
    def opponent_pos(q_out, q_o):
        opponent_possessions = {}
        technical = {}
        possessions = 0
        q_remove = []
        ftc = 0
        tech_count = 0
        repeat_time = 1001
        for q in q_out:
            if repeat_time != int(q[0].replace(":", "")):
                repeat_time = int(q[0].replace(":", ""))
                for action in q_o:
                    if int(action[0].replace(":", "")) >= int(q[0].replace(":", "")):
                        # TODO what is 2 free throws?/ "made" is in free throw (and one vs make two)
                        if ("missed free throw" in action[1]) or ("made free throw" in action[1]):
                            ftc += 1
                            if ftc >= 2:
                                possessions += ftc*0.5
                                ftc = 0
                        elif ("made" in action[1]) or ("missed" in action[1]) or ("Turnover" in action[1]):
                            possessions += 1
                            ftc = 0
                        elif "offensive" in action[1]:
                            possessions -= 1
                            ftc = 0
                        elif "TEAM deadball rebound" in action[1]:
                            # if dead ball as offensive rebound
                            possessions -= 1
                            # if dead ball in between two free throws, then want to add back -1 taken
                            ftc += 2
                        elif "Technical Foul" in action[1]:
                            tech_count += 1
                        q_remove.append([action[0], action[1]])
                    else:
                        break
                technical[">" + q[0]] = tech_count
                opponent_possessions[">" + q[0]] = math.floor(possessions)
                for t, p in q_remove:
                    q_o.remove([t, p])
                q_remove = []
                possessions = 0
                ftc = 0
                tech_count = 0
        if len(q_o) > 0:
            if "offensive rebound" in q_o[-1][1]:
                del q_o[-1]
        for play2 in q_o:
            if ("missed free throw" in play2[1]) or ("made free throw" in play2[1]):
                ftc += 1
                if ftc >= 2:
                    possessions += ftc * 0.5
                    ftc = 0
            elif ("made" in play2[1]) or ("missed" in play2[1]) or ("Turnover" in play2[1]):
                possessions += 1
                ftc = 0
            elif "offensive" in play2[1]:
                possessions -= 1
                ftc = 0
            elif "Technical Foul" in play2[1]:
                tech_count += 1
        opponent_possessions[">0"] = math.floor(possessions)
        technical[">0"] = tech_count
        return opponent_possessions, technical


    # Function that counts statistics (pts, rebounds, fta, fga, and threes)
    def stat(q_out, q_o):
        stats = {}
        q_remove = []
        fta = 0
        fga = 0
        threepa = 0
        rebounds = 0
        pts = 0
        repeat_time = 1001
        for q in q_out:
            if repeat_time != int(q[0].replace(":", "")):
                repeat_time = int(q[0].replace(":", ""))
                for action in q_o:
                    if int(action[0].replace(":", "")) >= int(q[0].replace(":", "")):
                        if ("made jump shot" in action[1]) or ("made layup" in action[1])  or ("made tip-in" in action[1]):
                            fga += 1
                            pts += 2
                        elif "made 3-pt." in action[1]:
                            fga += 1
                            threepa += 1
                            pts += 3
                        elif ("missed jump shot" in action[1]) or ("missed layup" in action[1]) or ("missed tip-in" in action[1]):
                            fga += 1
                        elif "missed 3-pt" in action[1]:
                            fga += 1
                            threepa += 1
                        elif ("offensive rebound" in action[1]) or ("defensive rebound" in action[1]):
                            rebounds += 1
                        elif "made free throw" in action[1]:
                            fta += 1
                            pts += 1
                        elif "missed free throw" in action[1]:
                            fta += 1
                        q_remove.append([action[0], action[1]])
                    else:
                        break
                stats[">" + q[0]] = [pts, threepa, fga, fta, rebounds]
                for t, p in q_remove:
                    q_o.remove([t, p])
                q_remove = []
                fta = 0
                fga = 0
                threepa = 0
                rebounds = 0
                pts = 0
        for play2 in q_o:
            if ("made jump shot" in play2[1]) or ("made layup" in play2[1]) or ("made tip-in" in play2[1]):
                fga += 1
                pts += 2
            elif "made 3-pt." in play2[1]:
                fga += 1
                threepa += 1
                pts += 3
            elif ("missed jump shot" in play2[1]) or ("missed layup" in play2[1]) or ("missed tip-in" in play2[1]):
                fga += 1
            elif "missed 3-pt" in play2[1]:
                fga += 1
                threepa += 1
            elif ("offensive rebound" in play2[1]) or ("defensive rebound" in play2[1]):
                rebounds += 1
            elif "made free throw" in play2[1]:
                fta += 1
                pts += 1
            elif "missed free throw" in play2[1]:
                fta += 1
        stats[">0"] = [pts, threepa, fga, fta, rebounds]
        return stats


    # dictionaries of possessions for each lineup in each quarter for both teams
    o_q1 = opponent_pos(q1_out, q1_o.copy())
    o_q2 = opponent_pos(q2_out, q2_o.copy())
    o_q3 = opponent_pos(q3_out, q3_o.copy())
    o_q4 = opponent_pos(q4_out, q4_o.copy())
    o_ot = opponent_pos(ot_out, ot_o.copy())

    cmu_q1 = opponent_pos(q1_out, q1_cmu.copy())
    cmu_q2 = opponent_pos(q2_out, q2_cmu.copy())
    cmu_q3 = opponent_pos(q3_out, q3_cmu.copy())
    cmu_q4 = opponent_pos(q4_out, q4_cmu.copy())
    cmu_ot = opponent_pos(ot_out, ot_cmu.copy())


    # dictionaries of stats for each lineup in each quarter for both teams
    oD_q1 = stat(q1_out, q1_o)
    oD_q2 = stat(q2_out, q2_o)
    oD_q3 = stat(q3_out, q3_o)
    oD_q4 = stat(q4_out, q4_o)
    oD_ot = stat(ot_out, ot_o)

    cmuD_q1 = stat(q1_out, q1_cmu)
    cmuD_q2 = stat(q2_out, q2_cmu)
    cmuD_q3 = stat(q3_out, q3_cmu)
    cmuD_q4 = stat(q4_out, q4_cmu)
    cmuD_ot = stat(ot_out, ot_cmu)


    end = q1_out[0][0].split(":")
    minutes_s_play = str(10-int(end[0])-1) + ":" + str(60-int(end[1]))
    min_played = int(minutes_s_play.split(":")[0]) + (int(minutes_s_play.split(":")[1]) / 60)
    full_data = {"LINEUP (NAMES)": [starting_lineup], "NUMBERS": [number_players(starting_lineup)], "SCORE": [f'{cmu_score}-{opponent_score}'], "LOCATION": [tag], "NUMBER OF GUARDS": [num_guards(starting_lineup)],
                 "OPPONENT POSSESSIONS": [o_q1[0][">" + q1_out[0][0]] - cmu_q1[1][">" + q1_out[0][0]]],
                 "CMU POSSESSIONS": [cmu_q1[0][">" + q1_out[0][0]] - o_q1[1][">" + q1_out[0][0]]],
                 "LINEUP MINUTES": [minutes_s_play], "OPPONENT PTS": [oD_q1[">" + q1_out[0][0]][0]], "CMU PTS": [cmuD_q1[">" + q1_out[0][0]][0]],
                 "SCORE DIFFERENTIAL WHEN ENTER": [0], "CMU 3PA": [cmuD_q1[">" + q1_out[0][0]][1]], "CMU FGA": [cmuD_q1[">" + q1_out[0][0]][2]],
                 "CMU FTA": [cmuD_q1[">" + q1_out[0][0]][3]], "CMU REBOUNDS": [cmuD_q1[">" + q1_out[0][0]][4]],
                 "TOTAL REBOUNDS": [oD_q1[">" + q1_out[0][0]][4] + cmuD_q1[">" + q1_out[0][0]][4]], "QUARTER": [1]}

    s_diff = cmuD_q1[">" + q1_out[0][0]][0] - oD_q1[">" + q1_out[0][0]][0]


    def minutes_played(min1, sec1, min2, sec2):
        seconds = sec1 + (60 - sec2)
        minutes = min1 - min2 - 1
        if seconds >= 60:
            seconds = seconds - 60
            minutes += 1
        return f"{minutes:02d}:{seconds:02d}"


    def add_times(time1, time2):
        min1 = int(time1.split(":")[0])
        sec1 = int(time1.split(":")[1])
        min2 = int(time2.split(":")[0])
        sec2 = int(time2.split(":")[1])
        seconds = sec1 + sec2
        minutes = min1 + min2
        if seconds >= 60:
            seconds = seconds - 60
            minutes += 1
        return f"{minutes:02d}:{seconds:02d}"


    def add_table(q_out, q_in, new_lineup, o_q, cmu_q, next_q_out, next_q_o, next_cmu_o,
                  oD_q, cmuD_q, next_q_oD, next_cmuD_q, sd):
        first_time = q_out[0][0]
        s_d = sd
        min_part = int(q_out[0][0].split(":")[0])
        sec_part = int(q_out[0][0].split(":")[1])
        for p_out, p_in in zip(q_out, q_in):
            if p_out[0] == first_time:
                new_lineup = new_lineup.replace(p_out[1], p_in[1])
            else:
                lineup_min = minutes_played(min_part, sec_part, int(p_out[0].split(":")[0]), int(p_out[0].split(":")[1]))
                min_part = int(p_out[0].split(":")[0])
                sec_part = int(p_out[0].split(":")[1])
                full_data["LINEUP (NAMES)"].append(new_lineup)
                full_data["NUMBERS"].append(number_players(new_lineup))
                full_data["SCORE"].append(f'{cmu_score}-{opponent_score}')
                full_data["LOCATION"].append(tag)
                full_data["NUMBER OF GUARDS"].append(num_guards(new_lineup))
                full_data["OPPONENT POSSESSIONS"].append(o_q[0][">" + p_out[0]] - cmu_q[1][">" + p_out[0]])
                full_data["CMU POSSESSIONS"].append(cmu_q[0][">" + p_out[0]] - o_q[1][">" + p_out[0]])
                full_data["LINEUP MINUTES"].append(lineup_min)
                min_played = int(lineup_min.split(":")[0]) + (int(lineup_min.split(":")[1])/60)
                full_data["OPPONENT PTS"].append(oD_q[">" + p_out[0]][0])
                full_data["CMU PTS"].append(cmuD_q[">" + p_out[0]][0])
                full_data["SCORE DIFFERENTIAL WHEN ENTER"].append(s_d)
                full_data["CMU 3PA"].append(cmuD_q[">" + p_out[0]][1])
                full_data["CMU FGA"].append(cmuD_q[">" + p_out[0]][2])
                full_data["CMU FTA"].append(cmuD_q[">" + p_out[0]][3])
                full_data["CMU REBOUNDS"].append(cmuD_q[">" + p_out[0]][4])
                full_data["TOTAL REBOUNDS"].append(oD_q[">" + p_out[0]][4] + cmuD_q[">" + p_out[0]][4])
                full_data["QUARTER"].append(p_out[3])
                first_time = p_out[0]
                new_lineup = new_lineup.replace(p_out[1], p_in[1])
                s_d += (cmuD_q[">" + p_out[0]][0] - oD_q[">" + p_out[0]][0])
        values = []
        values_od = []
        values_cmud = []
        tf = []
        for val1, val2 in zip(next_q_o[0].values(), next_cmu_o[0].values()):
            values.append(val1)
            values.append(val2)
        for tf1, tf2 in zip(next_q_o[1].values(), next_cmu_o[1].values()):
            tf.append(tf1)
            tf.append(tf2)
        for val1, val2 in zip(next_q_oD.values(), next_cmuD_q.values()):
            values_od.append(val1)
            values_cmud.append(val2)
        lineup_min = minutes_played(10, 00, int(next_q_out[0][0].split(":")[0]), int(next_q_out[0][0].split(":")[1]))
        end_lineup_time = add_times(p_out[0], lineup_min)
        min_played = int(end_lineup_time.split(":")[0]) + (int(end_lineup_time.split(":")[1]) / 60)
        full_data["LINEUP (NAMES)"].append(new_lineup)
        full_data["NUMBERS"].append(number_players(new_lineup))
        full_data["SCORE"].append(f"{cmu_score}-{opponent_score}")
        full_data["LOCATION"].append(tag)
        full_data["NUMBER OF GUARDS"].append(num_guards(new_lineup))
        full_data["OPPONENT POSSESSIONS"].append((o_q[0][">0"] + values[0]) - (cmu_q[1][">0"] + tf[1]))
        full_data["CMU POSSESSIONS"].append((cmu_q[0][">0"] + values[1]) - (o_q[1][">0"] + tf[0]))
        full_data["LINEUP MINUTES"].append(end_lineup_time)
        full_data["OPPONENT PTS"].append(oD_q[">0"][0] + values_od[0][0])
        full_data["CMU PTS"].append(cmuD_q[">0"][0] + values_cmud[0][0])
        full_data["SCORE DIFFERENTIAL WHEN ENTER"].append(s_d)
        full_data["CMU 3PA"].append(cmuD_q[">0"][1] + values_cmud[0][1])
        full_data["CMU FGA"].append(cmuD_q[">0"][2] + values_cmud[0][2])
        full_data["CMU FTA"].append(cmuD_q[">0"][3] + values_cmud[0][3])
        full_data["CMU REBOUNDS"].append(cmuD_q[">0"][4] + values_cmud[0][4])
        full_data["TOTAL REBOUNDS"].append(oD_q[">0"][4] + values_od[0][4] + cmuD_q[">0"][4] + values_cmud[0][4])
        full_data["QUARTER"].append(p_out[3])
        s_d += ((cmuD_q[">0"][0] + values_cmud[0][0]) - (oD_q[">0"][0] + values_od[0][0]))
        return new_lineup, s_d


    end_q1 = add_table(q1_out, q1_in, starting_lineup, o_q1, cmu_q1, q2_out, o_q2, cmu_q2, oD_q1, cmuD_q1, oD_q2, cmuD_q2,
                       s_diff)
    end_q2 = add_table(q2_out, q2_in, end_q1[0], o_q2, cmu_q2, q3_out, o_q3, cmu_q3, oD_q2, cmuD_q2, oD_q3, cmuD_q3,
                       end_q1[1])
    end_q3 = add_table(q3_out, q3_in, end_q2[0], o_q3, cmu_q3, q4_out, o_q4, cmu_q4, oD_q3, cmuD_q3, oD_q4, cmuD_q4,
                       end_q2[1])

    if len(ot_o) > 0:
        if len(ot_out) > 0:
            end_q4 = add_table(q4_out, q4_in, end_q3[0], o_q4, cmu_q4, ot_out, o_ot, cmu_ot, oD_q4,
                               cmuD_q4, oD_ot, cmuD_ot, end_q3[1])
            end_ot = add_table(ot_out, ot_in, end_q4[0], o_ot, cmu_ot, [["5:00", "no one"]], ({"o": 0},{"o": 0}), ({"o": 0}, {"o": 0}), oD_ot,
                               cmuD_ot, {"o": [0, 0, 0, 0, 0]}, {"o": [0, 0, 0, 0, 0]}, end_q4[1])
        else:
            end_q4 = add_table(q4_out, q4_in, end_q3[0], o_q4, cmu_q4, [["5:00", "no one", "score", 'OT']], o_ot, cmu_ot,
                               oD_q4, cmuD_q4, oD_ot, cmuD_ot, end_q3[1])
    else:
        end_q4 = add_table(q4_out, q4_in, end_q3[0], o_q4, cmu_q4, [["10:00", "no one"]], ({"o": 0}, {"o": 0}), ({"o": 0}, {"o": 0}), oD_q4,
                           cmuD_q4, {"o": [0, 0, 0, 0, 0]}, {"o": [0, 0, 0, 0, 0]}, end_q3[1])

    df = pd.DataFrame(full_data)
    folder_path = "extended_cmu_data"
    full_path = os.path.join(folder_path, "extended_cmu_data_" + season + "_" + opponent.lower() + ".csv")
    os.makedirs(folder_path, exist_ok=True)
    df.to_csv(full_path, index=True)

file_path = os.path.join("dictionaries", season + "_game_order.txt")
with open(file_path, "w") as file:
    file.write(game_order.strip(",") + "\n")

file.close()

