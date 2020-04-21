FORMAT_ARENA_RANK_DOWN = {
	"author": {
		"name": "${user}",
		"icon_url": "${user.avatar}"
	},
	"title": "Got kicked back",
	"thumbnail": {
		"url": "${server}/media/sabers.png"
	},
	"description": "In *Squad Arena*\n```Rank ${old.rank} ➘ ${new.rank}```"
}

FORMAT_ARENA_RANK_UP = {
	"author": {
		"name": "${user}",
		"icon_url": "${user.avatar}"
	},
	"title": "Moved up",
	"thumbnail": {
		"url": "${server}/media/sabers.png"
	},
	"description": "In *Squad Arena*\n```Rank ${old.rank} ➚ ${new.rank}```"
}

FORMAT_FLEET_RANK_DOWN = {
	"author": {
		"name": "${user}",
		"icon_url": "${user.avatar}"
	},
	"title": "Got kicked back",
	"thumbnail": {
		"url": "${server}/media/milf.png"
	},
	"description": "In *Fleet Arena*\n```Rank ${old.rank} ➘ ${new.rank}```"
}

FORMAT_FLEET_RANK_UP = {
	"author": {
		"name": "${user}",
		"icon_url": "${user.avatar}"
	},
	"title": "Moved up",
	"thumbnail": {
		"url": "${server}/media/milf.png"
	},
	"description": "In *Fleet Arena*\n```Rank ${old.rank} ➚ ${new.rank}```"
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
	"description": "\ud83d\udeab **${user}** has been slacking away!!! \ud83d\udecf\ufe0f\ud83d\udca4\ud83d\udc7b\ud83d\udc4e\n\u274c Be __**Smart**__ buddy! \ud83d\ude0e \ud83d\ude07\n\u26d4 Don't let \ud83d\udca2Rooster's \ud83e\uddb6 into your \ud83c\udf51\n\ud83d\ude21 Or you **WILL** regret it! \ud83d\udcaa\ud83e\uddb7 \u2620\ufe0f\ud83d\udc80\ud83d\udc7b \n```Slacking for ${last.seen}```"
}

FORMAT_PLAYER_NICK = {
	"author": {
		"name": "${user}",
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
		"name": "${user}",
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
		"name": "${user}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/avatar/${unit.id}?level=${level}&rarity=${rarity}&gear=${gear}&zetas=${zetas}&relics=${relic}&alignment=${alignment}"
	},
	"title": "${unit}",
	"description": "***Gear ${roman.gear}***",
	"image": {
		"url": "${server}/avatar/${unit.id}?gear=${gear}&alignment=${alignment}"
	}
}

FORMAT_UNIT_GEAR_PIECE = {
	"author": {
		"name": "${user}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/avatar/${unit.id}?level=${level}&rarity=${rarity}&gear=${gear}&zetas=${zetas}&relics=${relic}&alignment=${alignment}"
	},
	"title": "${unit}",
	"description": "***${equip}***",
	"image": {
		"url": "${server}/gear/${equip.id}/"
	}
}

FORMAT_UNIT_LEVEL = {
	"author": {
		"name": "${user}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/avatar/${unit.id}?level=${level}&rarity=${rarity}&gear=${gear}&zetas=${zetas}&relics=${relic}&alignment=${alignment}"
	},
	"title": "${unit}",
	"description": "***Level ${level}***",
	"image": {
		"url": "${server}/avatar/${unit.id}?level=${level}"
	}
}

FORMAT_UNIT_OMEGA = {
	"author": {
		"name": "${user}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/avatar/${unit.id}?level=${level}&rarity=${rarity}&gear=${gear}&zetas=${zetas}&relics=${relic}&alignment=${alignment}"
	},
	"title": "${unit}",
	"description": "***${skill}***",
	"image": {
		"url": "${server}/media/omega.png"
	}
}

FORMAT_UNIT_SKILL_INCREASED = {
	"author": {
		"name": "${user}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/avatar/${unit.id}?level=${level}&rarity=${rarity}&gear=${gear}&zetas=${zetas}&relics=${relic}&alignment=${alignment}"
	},
	"title": "${unit}",
	"description": "***${skill}***\n```Tier ${tier}```",
	"image": {
		"url": "${server}/skill/${skill.id}/"
	}
}

FORMAT_UNIT_SKILL_UNLOCKED = {
	"author": {
		"name": "${user}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/avatar/${unit.id}?level=${level}&rarity=${rarity}&gear=${gear}&zetas=${zetas}&relics=${relic}&alignment=${alignment}"
	},
	"title": "${unit}",
	"description": "***${skill}***\n```Unlocked```",
	"image": {
		"url": "${server}/skill/${skill.id}/"
	}
}

FORMAT_UNIT_RARITY = {
	"author": {
		"name": "${user}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/avatar/${unit.id}?level=${level}&rarity=${rarity}&gear=${gear}&zetas=${zetas}&relics=${relic}&alignment=${alignment}"
	},
	"title": "${unit}",
	"description": "${stars}",
	"image": {
		"url": "${server}/avatar/${unit.id}?rarity=${rarity}"
	}
}

FORMAT_UNIT_RELIC = {
	"author": {
		"name": "${user}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/avatar/${unit.id}?level=${level}&rarity=${rarity}&gear=${gear}&zetas=${zetas}&relics=${relic}&alignment=${alignment}"
	},
	"title": "${unit}",
	"description": "***Relic ${relic}***",
	"image": {
		"url": "${server}/relic/${relic}/${alignment}/"
	}
}

FORMAT_UNIT_UNLOCKED = {
	"author": {
		"name": "${user}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/avatar/${unit.id}"
	},
	"title": "Unlocked",
	"description": "***${unit}***",
	"image": {
		"url": "${server}/avatar/${unit.id}"
	}
}

FORMAT_UNIT_ZETA = {
	"author": {
		"name": "${user}",
		"icon_url": "${user.avatar}"
	},
	"thumbnail": {
		"url": "${server}/avatar/${unit.id}?level=${level}&rarity=${rarity}&gear=${gear}&zetas=${zetas}&relics=${relic}&alignment=${alignment}"
	},
	"title": "${unit}",
	"description": "***${skill}***",
	"image": {
		"url": "${server}/media/zeta.png"
	}
}
