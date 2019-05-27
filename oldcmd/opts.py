
def parse_opts_ally_code(config, author, arg):

	ally_code = Player.get_ally_code_by_nick(arg)
	if ally_code:
		return ally_code

	if len(arg) >= 11 and len(arg.split('-')) == 3:
		arg = ''.join(arg.split('-'))

	if len(arg) >= 9 and arg.isdigit():
		return arg

	return None

def parse_opts_lang(args):

	args_cpy = list(args)
	for arg in args_cpy:

		if arg in [ 'en', 'EN', 'english' ]:
			args.remove(arg)
			return args, 'en'

		if arg in [ 'fr', 'FR', 'french' ]:
			args.remove(arg)
			return args, 'fr'

	return args, 'en'

