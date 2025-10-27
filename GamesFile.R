library("rmarkdown")
library("stringr")

list_files <- list.files('/Users/nicoletimko/Desktop/SURA project code/extended_cmu_data', pattern = "\\.csv$", full.names = TRUE)

games <- list()

individual_games <- tibble("GAME" = character(), "SCORE" = character(), "LOCATION" = character(), "3G" = integer(), "4G" = integer(), "3G MEDIAN NET RATING" = numeric(), "4G MEDIAN NET RATING" = numeric(), "NET RATING DIFFERENCE" = numeric(), "NET RATING MANN-WHITNEY P-VALUE" = numeric(), "3G MEDIAN TRB%" = numeric(), "4G MEDIAN TRB%" = numeric(), "TRB% DIFFERENCE" = numeric(), "TRB% MANN-WHITNEY P-VALUE" = numeric(), "3G MEDIAN 3PA/FGA" = numeric(), "4G MEDIAN 3PA/FGA" = numeric(), "3PA/FGA DIFFERENCE" = numeric(), "3PA/FGA MANN-WHITNEY P-VALUE" = numeric(), "3G MEDIAN TRUE SHOOTING %" = numeric(), "4G MEDIAN TRUE SHOOTING %" = numeric(), "TRUE SHOOTING % DIFFERENCE" = numeric(), "TRUE SHOOTING % MANN-WHITNEY P-VALUE" = numeric(), "3G MEDIAN PACE" = numeric(), "4G MEDIAN PACE" = numeric(), "PACE DIFFERENCE" = numeric(), "PACE MANN-WHITNEY P-VALUE" = numeric(),"3G MEDIAN DEFENSIVE RATING" = numeric(), "4G MEDIAN DEFENSIVE RATING" = numeric(), "DEFENSIVE RATING DIFFERENCE" = numeric(), "DEFENSIVE RATING MANN-WHITNEY P-VALUE" = numeric(), "3G MEDIAN OFFENSIVE RATING" = numeric(), "4G MEDIAN OFFENSIVE RATING" = numeric(), "OFFENSIVE RATING DIFFERENCE" = numeric(), "OFFENSIVE RATING MANN-WHITNEY P-VALUE" = numeric())

for (f in list_files){
  df <- read.csv(f, check.names = FALSE)
  has_three <- any(df$`NUMBER OF GUARDS` == 3, na.rm = TRUE)
  has_four <- any(df$`NUMBER OF GUARDS` == 4, na.rm = TRUE)
  if (has_three & has_four){
    opponent <- str_remove(f, ".*/extended_cmu_data_")
    season_opponent <- str_remove(opponent, ".csv")
    season_opponent_vector <- strsplit(season_opponent, "_")
    opponent_name <- season_opponent_vector[[1]][3]
    season_name <- paste(season_opponent_vector[[1]][1], season_opponent_vector[[1]][2], sep= "_")
    games <- c(games, opponent_name)
  }
}

dir.create("/Users/nicoletimko/Desktop/SURA project code/sing_game_EDA/", showWarnings = FALSE, recursive = TRUE)

for (g in games){
  rmarkdown::render(
    input = "singular_game_pos.Rmd",
    output_file = paste0(sn, "_", g,"_EDA.pdf"),
    params = list(category = g, year = season_name),
    output_dir = "/Users/nicoletimko/Desktop/SURA project code/sing_game_EDA/"
  )
}

#EDA4 and individual_games is cutting at score differential
#EDA5 and individual_games5 is cutting at score differential and over 1 minute

write.csv(individual_games,glue("~/Desktop/SURA project code/data frames/", sn, "_individual_games.csv"))

