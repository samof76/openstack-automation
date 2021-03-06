# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 10:16:23 2013

@author: akilesh
"""

# -*- coding: utf-8 -*-
'''
Management of MySQL grants (user permissions).
==============================================

:depends:   - MySQLdb Python module
:configuration: See :py:mod:`salt.modules.mysql` for setup instructions.

The mysql_grants module is used to grant and revoke MySQL permissions.

The ``name`` you pass in purely symbolic and does not have anything to do
with the grant itself.

The ``database`` parameter needs to specify a 'priv_level' in the same
specification as defined in the MySQL documentation:

* \\*
* \\*.\\*
* db_name.\\*
* db_name.tbl_name
* etc...

.. code-block:: yaml

   frank_exampledb:
      mysql_grants.present:
       - grant: select,insert,update
       - database: exampledb.*
       - user: frank
       - host: localhost

   frank_otherdb:
     mysql_grants.present:
       - grant: all privileges
       - database: otherdb.*
       - user: frank

   restricted_singletable:
     mysql_grants.present:
       - grant: select
       - database: somedb.sometable
       - user: joe
'''

import sys


def __virtual__():
    '''
    Only load if the mysql module is available
    '''
    return 'mysql_grants' if 'mysql.grant_exists' in __salt__ else False


def _get_mysql_error():
    '''
    Look in module context for a MySQL error. Eventually we should make a less
    ugly way of doing this.
    '''
    return sys.modules[
        __salt__['test.ping'].__module__
    ].__context__.pop('mysql.error', None)


def present(name,
            grant=None,
            database=None,
            user=None,
            host='localhost',
            password=None,
            grant_option=False,
            escape=True,
            **connection_args):
    '''
    Ensure that the grant is present with the specified properties

    name
        The name (key) of the grant to add

    grant
        The grant priv_type (i.e. select,insert,update OR all privileges)

    database
        The database priv_level (ie. db.tbl OR db.*)

    user
        The user to apply the grant to

    host
        The network/host that the grant should apply to

    password
        The password to use

    grant_option
        Adds the WITH GRANT OPTION to the defined grant. default: False

    escape
        Defines if the database value gets escaped or not. default: True
    '''
    comment = 'Grant {0} on {1} to {2}@{3} is already present'
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': comment.format(grant, database, user, host)
           }
    # check if grant exists
    if __salt__['mysql.grant_exists'](
        grant, database, user, host, grant_option, escape, **connection_args
    ):
        return ret
    else:
        err = _get_mysql_error()
        if err is not None:
            ret['comment'] = err
            ret['result'] = False
            return ret

    # The grant is not present, make it!
    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'MySQL grant {0} is set to be created'.format(name)
        return ret
    if __salt__['mysql.grant_add'](
        grant, database, user, host, password,
        grant_option, escape, **connection_args
    ):
        ret['comment'] = 'Grant {0} on {1} to {2}@{3} has been added'
        ret['comment'] = ret['comment'].format(grant, database, user, host)
        ret['changes'][name] = 'Present'
    else:
        ret['comment'] = 'Failed to execute: "GRANT {0} ON {1} TO {2}@{3}"'
        ret['comment'] = ret['comment'].format(grant, database, user, host)
        err = _get_mysql_error()
        if err is not None:
            ret['comment'] += ' ({0})'.format(err)
        ret['result'] = False
    return ret


def absent(name,
           grant=None,
           database=None,
           user=None,
           host='localhost',
           grant_option=False,
           escape=True,
           **connection_args):
    '''
    Ensure that the grant is absent

    name
        The name (key) of the grant to add

    grant
        The grant priv_type (i.e. select,insert,update OR all privileges)

    database
        The database priv_level (i.e. db.tbl OR db.*)

    user
        The user to apply the grant to

    host
        The network/host that the grant should apply to
    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    # Check if grant exists, and if so, remove it
    if __salt__['mysql.grant_exists'](
            grant,
            database,
            user, host,
            grant_option,
            escape,
            **connection_args):

        if __opts__['test']:
            ret['result'] = None
            ret['comment'] = 'MySQL grant {0} is set to be revoked'
            ret['comment'] = ret['comment'].format(name)
            return ret
        if __salt__['mysql.grant_revoke'](
                grant,
                database,
                user,
                host,
                grant_option,
                **connection_args):
            ret['comment'] = 'Grant {0} on {1} for {2}@{3} has been revoked'
            ret['comment'] = ret['comment'].format(grant, database, user,
                                                   host)
            ret['changes'][name] = 'Absent'
            return ret
        else:
            err = _get_mysql_error()
            if err is not None:
                ret['comment'] = 'Unable to revoke grant {0} on {1} for ' \
                                 '{2}@{3} ({4})'.format(grant, database,
                                                        user, host, err)
                ret['result'] = False
                return ret
    else:
        err = _get_mysql_error()
        if err is not None:
            ret['comment'] = 'Unable to determine if grant {0} on {1} for ' \
                             '{2}@{3} exists ({4})'.format(grant, database,
                                                           user, host, err)
            ret['result'] = False
            return ret

    # fallback
    ret['comment'] = ('Grant {0} on {1} to {2}@{3} is not present, so it'
                      ' cannot be revoked').format(
                              grant,
                              database,
                              user,
                              host
                              )
    return ret
