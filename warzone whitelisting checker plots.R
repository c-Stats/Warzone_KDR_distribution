library(data.table)
library(dplyr)
library(ggplot2)
library(stringr)

library(reshape2)


path <- "D:/CoD_data/"
names <- c("FrankFredj%231458", "Huskerrs", "SwaggXBL")

frames <- lapply(as.list(names), function(x){fread(paste(path, x, ".csv", sep = ""))})
names(frames) <- names

#format dates
i <- 1
for(f in frames){

	if("V1" %in% names(f)){

		f[, V1 := NULL]

	}

	#remove hackers

	index <- f[grepl("PM", Time), which = TRUE]
	
	f[index, Hour := as.numeric(str_split(f$Time[index], ":", n = 2, simplify = TRUE)[, 1]) + 12]
	f[-index, Hour := as.numeric(str_split(f$Time[-index], ":", n = 2, simplify = TRUE)[, 1])]

	f[, Minute := as.numeric(str_split(f$Time, ":", n = 3, simplify = TRUE)[, 2])]

	f[Minute > 30, Hour := Hour + 1]
	f[Hour == 25, Hour := 1]

	f[, Time_Group := paste("TimeGroup", floor((Hour - 1) / 3), sep = "")]
	f[, Player := names[i]]

	f[, Date := NULL] %>%
		.[, Time := NULL] %>%
		.[, Hour := NULL] %>%
		.[, Minute := NULL] 

	i <- i + 1

}

frames <- dplyr::bind_rows(frames)

#Remove hackers
frames <- frames[KDR <= 7.5] 

frames <- frames[(grepl("BR", Mode) | grepl("Resurgence", Mode)) & !(grepl("Buyback", Mode))]

frames[grepl("BR", Mode), Mode := "BR"] %>%
		.[grepl("Resurgence", Mode), Mode := "Resurgence"]

frames[, (names(frames)[sapply(frames, is.character)]) := lapply(.SD, as.factor), .SDcols = names(frames)[sapply(frames, is.character)]]


#fixed effects model
fixed_effect_model <- lm(KDR ~., frames)

anova_table <- anova(fixed_effect_model)
individual_p_vals <- summary(fixed_effect_model)$coefficients

#Remove Resurgence since streamers don't play it that much
#Also, it seems like SBMM works differently in BR vs Resurgence

frames <- frames[Mode == "BR"] %>%
					.[, Mode := NULL]


#Re-fit model after deleting Mode
fixed_effect_model <- lm(KDR ~., frames)

anova_table <- anova(fixed_effect_model)
individual_p_vals <- summary(fixed_effect_model)$coefficients



#BR plot
#Remove the effect due to game mode, and game time
coefficients <- coef(fixed_effect_model)
coefficients <- coefficients[which(grepl("Player", names(coefficients)))]
coefficients_names <- names(coefficients)

adjusted_kdr <- frames[, c("KDR", "Player"), with = FALSE] %>%
						.[, Adjustment := 0]

for(i in 1:length(coefficients)){

	j <- str_remove(names(coefficients[i]), "Player")
	adjusted_kdr[Player == j, Adjustment := coefficients[i]] 

}

adjusted_kdr[, KDR := fixed_effect_model$residuals + 
						coef(fixed_effect_model)[1] +
						Adjustment]

adjusted_kdr[, Adjustment := NULL]



#Plot
plot_frame <- melt(adjusted_kdr, id = "Player")
ggplot(plot_frame, aes(x = value, fill = Player)) + geom_density(alpha = 0.5)

sample_desc_stats <- lapply(as.list(c(length, mean, median, sd)),
							function(x){adjusted_kdr[, lapply(.SD, x), by = "Player", .SDcols = "KDR"]})

names(sample_desc_stats) <- c("length", "mean", "median", "sd")


#T-test
#Manually change the names within the query

t.test(adjusted_kdr[Player == "FrankFredj%231458"]$KDR,
			adjusted_kdr[Player == "Huskerrs"]$KDR)

t.test(adjusted_kdr[Player == "FrankFredj%231458"]$KDR,
			adjusted_kdr[Player == "SwaggXBL"]$KDR)		





