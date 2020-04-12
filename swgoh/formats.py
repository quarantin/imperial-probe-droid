FORMAT_ARENA_RANK_DOWN = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}"
	},
	"title": "Got his ass kicked",
	"thumbnail": {
		"url": "${server}/media/sabers.png"
	},
	"description": "In *Squad Arena*\n```Rank ${old.rank} \u21d8 ${new.rank}```"
}

FORMAT_ARENA_RANK_UP = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}"
	},
	"title": "Kicked someone\u2018s ass",
	"thumbnail": {
		"url": "${server}/media/sabers.png"
	},
	"description": "In *Squad Arena*\n```Rank ${old.rank} \u21d7 ${new.rank}```"
}

FORMAT_FLEET_RANK_DOWN = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}"
	},
	"title": "Got his ass kicked",
	"thumbnail": {
		"url": "${server}/media/milf.png"
	},
	"description": "In *Fleet Arena*\n```Rank ${old.rank} \u21d8 ${new.rank}```"
}

FORMAT_FLEET_RANK_UP = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}"
	},
	"title": "Kicked someone\u2018s ass",
	"thumbnail": {
		"url": "${server}/media/milf.png"
	},
	"description": "In *Fleet Arena*\n```Rank ${old.rank} \u21d7 ${new.rank}```"
}

FORMAT_INACTIVITY = {
	"title": "Inactivity detected! Code Red!",
	"author": {
		"name": "ALAAAAAARM!!!",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "https://i.imgur.com/RLkJC1X.png"
	},
	"description": "\ud83d\udeab **${nick}** has been slacking away!!! \ud83d\udecf\ufe0f\ud83d\udca4\ud83d\udc7b\ud83d\udc4e\n\u274c Be __**Smart**__ buddy! \ud83d\ude0e \ud83d\ude07\n\u26d4 Don't let \ud83d\udca2Rooster's \ud83e\uddb6 into your \ud83c\udf51\n\ud83d\ude21 Or you **WILL** regret it! \ud83d\udcaa\ud83e\uddb7 \u2620\ufe0f\ud83d\udc80\ud83d\udc7b \n```Slacking for ${last.seen}```"
}

FORMAT_PLAYER_NICK = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${user.avatar}"
	},
	"title": "Is Now Known As",
	"description": "***${new.nick}***"
}

FORMAT_PLAYER_LEVEL = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}",
	},
	"thumbnail": {
		"url": "${user.avatar}"
	},
	"title": "Has Reached",
	"description": "***Level ${level}***"
}

FORMAT_UNIT_GEAR_LEVEL = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/avatar/${unit.id}?gear=${gear.level}"
	},
	"title": "${unit}",
	"description": "***Gear ${gear.level.roman}***"
}

FORMAT_UNIT_GEAR_PIECE = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/gear/${gear.piece.id}/"
	},
	"title": "${unit}",
	"description": "***${gear.piece}***"
}

FORMAT_UNIT_LEVEL = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/avatar/${unit.id}?level=${level}"
	},
	"title": "${unit}",
	"description": "***Level ${level}***"
}

FORMAT_UNIT_OMEGA = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/media/omega.png"
	},
	"title": "${unit}",
	"description": "***${skill}***",
	"image": {
		"url": "${server}/avatar/${unit.id}"
	}
}

FORMAT_UNIT_SKILL_INCREASED = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/skill/${skill.id}/"
	},
	"title": "${unit}",
	"description": "Increased ***${skill}***\n```Tier ${tier}```",
	"image": {
		"url": "${server}/avatar/${unit.id}"
	}
}

FORMAT_UNIT_SKILL_UNLOCKED = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/skill/${skill.id}/"
	},
	"title": "${unit}",
	"description": "***${skill}***",
	"image": {
		"url": "${server}/avatar/${unit.id}"
	}
}

FORMAT_UNIT_RARITY = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/avatar/${unit.id}?rarity=${rarity}"
	},
	"title": "${unit}",
	"description": "${stars}"
}

FORMAT_UNIT_RELIC = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/relic/${relic}/${alignment}/"
	},
	"title": "${unit}",
	"description": "***Relic ${relic}***",
	"image": {
		"url": "${server}/avatar/${unit.id}"
	}
}

FORMAT_UNIT_UNLOCKED = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/avatar/${unit.id}"
	},
	"title": "Unlocked",
	"description": "***${unit}***"
}

FORMAT_UNIT_ZETA = {
	"author": {
		"name": "${nick}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/media/zeta.png"
	},
	"title": "${unit}",
	"description": "***${skill}***",
	"image": {
		"url": "${server}/avatar/${unit.id}"
	}
}
