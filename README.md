---
# LDAP management: j-user/juser.py

- `j-user`: "front end" executable script with a variety of subcommands meant to make things easy, like "search user" or "apply <profile> user"
- `juser.py`: "back end" script/module defining subcommands like "search user" or "apply <profile> user"
- `jldap/`: modules facilitating LDAP work. Ideally concise, generic code which is maintainable and extensible and makes dealing with LDAP less painful.
- `ldap.yml`: "base" ldap configuration file lacking credentials. Useful in docker containers when a pre-existing set of credentials doesn't exist and instead relies on environment variables LDAP_USER and LDAP_PASS.

## Examples

- `j-user -h`
- `j-user search some.user`
- `j-user audit /path/to/profiles -u some.user other.user`

## Testing

Using the unittest module, this project attempts to gain as much test coverage as possible.
- Notable exception: `jldap/jive.py`
 - The only way to test this would be using a Jive instance. For obvious reasons, Brewspace is out. Using a private, test instance, while possible, seems a bit much just to make sure we can GET, POST, and PUT stuff to Jive.

# AWS User management: j-aws/jaws.py

- `j-aws`: "front end" executable script. Allows searching users with subcommand "aws_users"
- `jawshelper.py`: "back end" script/module defining subcommands like "aws_users""
- `jaws/`: modules facilitating AWS  work. Ideally concise, generic code which is maintainable and extensible and makes dealing with AWS less painful.
- `~/.aws/credentials`: INI config file with app/secret keys for AWS accounts or role-arns for role assumption.

# Okta User management: j-okta/jokta.py

- `j-okta`: "front end" executable script with a subcommand "user_apps" to find apps per user.
- `jokta.py`: "back end" script/module defining subcommands like "user_apps"
- `okta/`: modules facilitating Okta work. Ideally concise, generic code which is maintainable and extensible and makes dealing with Okta less painful.
- `key.yml`: YAML config file containing Okta API key and, if necessary, Okta base url.
  - Note ".yml" vs ".yaml". This project stores LDAP profile YAML files as *.yaml, hence .gitignore tracks them but not *.yml.
