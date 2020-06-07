require(ggplot2)
require(reshape2)
require(tidyverse)

setwd("/Users/Maciej/GitRepos/PSIAM")
all_buildings = c('A1', 'A10', 'B1', 'B4', 'B5', 'B9', 'C2', 'C3', 'C5', 'C6', 'C7', 'C11', 'C16', 'D1', 'D2')
buildings_set_1 = c('B4', 'A1', 'C2', 'C5', 'A5', 'B8')
buildings_set_2 = c('B5', 'A10', 'C5')

for (building in buildings_set_1) {
  df <- read.csv(file=sprintf("NoOfUsers-%s-hourly.csv", building))
  plot <- ggplot(data=df, aes(x=hour, y=avg, group=1)) +
    geom_line(color="red") + 
    theme(axis.text.x = element_text(angle = 90)) +
    labs(title=sprintf("Œrednia liczba u¿ytkowników dla budynku %s w skali godzin", building), x = "Godzina", y = "Œrednia liczba u¿ytkowników")
  png(file=sprintf("/Users/Maciej/GitRepos/PSIAM/R/NoOfUsers-%s-hourly.png", building),
      width=450, height=320)
  print(plot)
  dev.off()
}
for (building in buildings_set_2) {
  df <- read.csv(file=sprintf("LoadChannelUtilization-%s-hourly.csv", building))
  plot <- ggplot(dat = melt(df, id.var="hour"), aes(x=hour, y=value)) + 
    geom_line(aes(colour=variable, group=variable)) +
    theme(axis.text.x = element_text(angle = 90)) +
    labs(title=sprintf("Wykorzystanie kanalu dla budynku %s w skali godzin", building), x = "Godzina", y = "Wykorzystanie kanalu", color = "") +
    scale_color_hue(labels = c("Maksimum", "Œrednia"))+
    theme(legend.position="bottom")
  png(file=sprintf("/Users/Maciej/GitRepos/PSIAM/R/ChannelUtilization-%s-hourly.png", building),
      width=450, height=320)
  print(plot)
  dev.off()
}

no_of_users_max = c()
no_of_users_avg = c()
no_of_users_max_to_avg = c()
poor_snr_avg = c()
channel_util_avg = c()
poor_to_all_users = c()
# channel_util_per_ap_avg = c()
for (building in all_buildings) {
  df <- read.csv(file=sprintf("NoOfUsers-%s-hourly.csv", building))
  no_of_users_avg = append(no_of_users_avg, floor(mean(df[['avg']])))
  no_of_users_max = append(no_of_users_max, floor(max(df[['max']])))
  no_of_users_max_to_avg = append(no_of_users_max_to_avg, round(floor(max(df[['max']])) / floor(mean(df[['avg']])), digits = 2))
  
  df <- read.csv(file=sprintf("PoorSNRClients-%s-monthly.csv", building))
  poor_snr_avg = append(poor_snr_avg, floor(mean(df[['avg']])))
  
  df <- read.csv(file=sprintf("LoadChannelUtilization-%s-monthly.csv", building))
  channel_util_avg = append(channel_util_avg, round(mean(df[['avg']]), digits = 2))
  
  df <- read.csv(file=sprintf("PoorSNRClients-NoOfUsers-%s-monthly.csv", building))
  poor_to_all_users = append(poor_to_all_users, round(mean(df[['avg']]), digits = 4)*100)
  # building_aps <- dplyr::filter(complete_data, grepl(sprintf("AP-%s-", building), apName, fixed = TRUE))
  # channel_util_per_ap_avg = append(channel_util_per_ap_avg, mean(building_aps[['NoOfUsers']]))
  # print(channel_util_per_ap_avg)
}
building_stats <- data.frame(all_buildings, no_of_users_max, no_of_users_avg, no_of_users_max_to_avg, poor_snr_avg, poor_to_all_users, channel_util_avg)

png(file=sprintf("/Users/Maciej/GitRepos/PSIAM/R/NoOfUsers-per-building.png", building),
    width=700, height=500)
ggplot(building_stats, aes(x=all_buildings, y=no_of_users_avg)) + 
  geom_bar(stat = "identity") +
  labs(title="Œrednia liczba u¿ytkowników dla budynków PWr", x = "Budynek", y = "Liczba u¿ytkowników") +
  geom_text(
    label=no_of_users_avg, 
    nudge_x = 0.0, nudge_y = 2.5, 
    check_overlap = T
  )
dev.off()

png(file=sprintf("/Users/Maciej/GitRepos/PSIAM/R/ChannelUtil-per-building.png", building),
    width=700, height=500)
ggplot(building_stats, aes(x=all_buildings, y=channel_util_avg)) + 
  geom_bar(stat = "identity") +
  labs(title="Œrednie wykorzystanie kanau w AP dla budynków PWr", x = "Budynek", y = "Wykorzystanie kana³u [%]") +
  geom_text(
    label=channel_util_avg, 
    nudge_x = 0.0, nudge_y = 1.0, 
    check_overlap = T
  )
dev.off()

png(file=sprintf("/Users/Maciej/GitRepos/PSIAM/R/users-and-snr-users.png", building),
    width=700, height=500)
ggplot(dat=melt(building_stats[,c("all_buildings", "no_of_users_avg", "poor_snr_avg")], id.var="all_buildings"), aes(fill=variable, x=all_buildings, y=value)) + 
  geom_bar(position="dodge", stat = "identity") +
  labs(title="Œrednia liczba u¿ytkowników i u¿ytkowników o s³abym SNR", x = "Budynek", y = "Liczba u¿ytkowników", fill = "") +
  scale_fill_hue(labels = c("U¿ytkownicy", "U¿ytkownicy o s³abym SNR")) +
  geom_text(
    aes(label=value), 
    nudge_x = 0.0, nudge_y = 2.5, 
    check_overlap = T
  ) +
  theme(legend.position="bottom")
dev.off()

png(file=sprintf("/Users/Maciej/GitRepos/PSIAM/R/PoorSNR-to-NoOfUsers-ratio.png", building),
    width=700, height=500)
ggplot(building_stats, aes(x=all_buildings, y=poor_to_all_users)) + 
  geom_bar(stat = "identity") +
  labs(title="Stosunek liczby u¿ytkowników ze slabym SNR do wszystkich u¿ytkowników", x = "Budynek", y = "Stosunek u¿. o sabym SNR do wszystkich [%]") +
  geom_text(
    label=poor_to_all_users, 
    nudge_x = 0.0, nudge_y = 1.0, 
    check_overlap = T
  )
dev.off()

png(file=sprintf("/Users/Maciej/GitRepos/PSIAM/R/NoOfUsers-avg-and-max.png", building),
    width=700, height=500)
ggplot(dat=melt(building_stats[,c("all_buildings", "no_of_users_avg", "no_of_users_max")], id.var="all_buildings"), aes(fill=variable, x=all_buildings, y=value)) + 
  geom_bar(position="dodge", stat = "identity") +
  labs(title="Œrednia i maksymalna liczba u¿ytkowników dla budynków PWr", x = "Budynek", y = "Liczba u¿ytkowników", fill = "") +
  scale_fill_hue(labels = c("U¿ytkownicy", "U¿ytkownicy o s³abym SNR")) +
  geom_text(
    aes(label=value), 
    nudge_x = 0.0, nudge_y = 10, 
    check_overlap = T
  ) +
  theme(legend.position="bottom")
dev.off()

png(file=sprintf("/Users/Maciej/GitRepos/PSIAM/R/max-to-avg-NoOfUsers-ratio.png", building),
    width=700, height=500)
ggplot(building_stats, aes(x=all_buildings, y=no_of_users_max_to_avg)) + 
  geom_bar(stat = "identity") +
  labs(title="Stosunek maksymalnej liczby u¿ytkowników do sredniej liczby u¿ytkowników dla budynków PWr", x = "Budynek", y = "Stosunek u¿. o sabym SNR do wszystkich [%]") +
  geom_text(
    label=no_of_users_max_to_avg, 
    nudge_x = 0.0, nudge_y = 0.3, 
    check_overlap = T
  )
dev.off()

channel_util_per_ap_avg <- read.csv(file="LoadChannelUtilization-monthly.csv")
channel_util_per_ap_avg <- aggregate(channel_util_per_ap_avg[, c("avg")], list(channel_util_per_ap_avg$apName), max)
channel_util_per_ap_avg <- head(channel_util_per_ap_avg[order(-channel_util_per_ap_avg$x),], 10)

apName <- channel_util_per_ap_avg[["Group.1"]]
avg <- channel_util_per_ap_avg[["x"]]
channel_util_per_ap_avg <- data.frame(apName, avg)

png(file=sprintf("/Users/Maciej/GitRepos/PSIAM/R/ChannelUtil-per-AP.png", building),
    width=700, height=500)
ggplot(channel_util_per_ap_avg, aes(x=apName, y=avg)) + 
  geom_bar(stat = "identity") +
  labs(title="Najbardziej obcia¿one AP", x = "", y = "Wykorzystanie kanalu [%]") +
  geom_text(
    label=sprintf("%0.2f", channel_util_per_ap_avg$avg), 
    nudge_x = 0.0, nudge_y = 1.5, 
    check_overlap = T
  ) + 
  theme(axis.text.x = element_text(angle = 90))
dev.off()