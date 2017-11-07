import graphene
from graphene import relay
from graphene.types.inputobjecttype import InputObjectType
from graphene_sqlalchemy import SQLAlchemyObjectType
from graphene_sqlalchemy.fields import SQLAlchemyConnectionField
from graphql.error.base import GraphQLError

from crm import db
from crm.apps.address.models import Address
from crm.apps.contact.models import Subgroup
from crm.graphql import BaseMutation, BaseQuery, AddressArguments
from .models import Contact


class ContactType(SQLAlchemyObjectType):
    # object.id in graphene contains internal
    # representation of id.
    # we add another uid field that will return obj.uid property
    # obj.uid returns obj.id if id is set
    uid = graphene.String()

    class Meta:
        model = Contact
        interfaces = (relay.Node,)
        name = model.__name__


class ContactQuery(BaseQuery):
    """
    we have 2 queries here contact and contacts
    """

    # no need for resplve_contacts function here
    contacts = SQLAlchemyConnectionField(ContactType)
    # contact query to return one contact and takes (uid) argument
    # uid is the original object.id in db
    contact = graphene.Field(ContactType, uid=graphene.String())

    def resolve_contact(self, context, uid):
        return ContactType.get_query(context).filter_by(id=uid).first()

    class Meta:
        interfaces = (relay.Node, )


class CreateContactArguments(InputObjectType):
    firstname = graphene.String(required=True)
    lastname = graphene.String()
    description = graphene.String()
    telegram = graphene.String()
    bio = graphene.String()
    emails = graphene.String(required=True)
    telephones = graphene.String(required=True)
    belief_statement = graphene.String()
    owner_id = graphene.String()
    ownerbackup_id = graphene.String()
    parent_id = graphene.String()
    tf_app = graphene.Boolean()
    tf_web = graphene.Boolean()
    country = graphene.String()
    message_channels = graphene.String()
    sub_groups = graphene.List(graphene.String)
    addresses = graphene.List(AddressArguments)


class UpdateContactContactArguments(CreateContactArguments):
    uid = graphene.String(required=True)
    firstname = graphene.String()
    emails = graphene.String()
    telephones = graphene.String()


class CreateContacts(graphene.Mutation):
    class Arguments:
        """
            Mutation Arguments        
        """
        records = graphene.List(CreateContactArguments, required=True)

    ok = graphene.Boolean()
    ids = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, context, **kwargs):
        """
        Mutation logic is handled here
        """

        # 'before_insert' hooks won't work with db.session.bulk_save_objects
        # we need to find a way to get hooks to work with bulk_save_objects @todo
        records = kwargs.get('records', [])
        objs = []
        for data in records:
            addresses = data.pop('addresses') if 'addresses' in data else []
            subgroups = data.pop('sub_groups') if 'sub_groups' in data else []
            c = Contact(**data)
            c.addresses = [ Address(**address) for address in addresses]
            c.subgroups = [Subgroup(groupname=subgroup) for subgroup in subgroups]
            # db.session.add(c)
            c.update_auto_fields()
            objs.append(c)
        try:
            db.session.info['changes'] = {'created': objs, 'updated': [], 'deleted':{}}
            db.session.bulk_save_objects(objs)
            db.session.commit()
            return cls(ok=True, ids=[obj.id for obj in objs])
        except Exception as e:
            raise GraphQLError(e.args)


class UpdateContacts(graphene.Mutation):
    class Arguments:
        """
            Mutation Arguments        
        """
        records = graphene.List(UpdateContactContactArguments, required=True)

    ok = graphene.Boolean()
    ids = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, context, **kwargs):
        """
        Mutation logic is handled here
        """

        # 'before_insert' hooks won't work with db.session.bulk_save_objects
        # we need to find a way to get hooks to work with bulk_save_objects @todo

        records = kwargs.get('records', [])
        for data in records:
            data['id'] = data.pop('uid')
            addresses = data.pop('addresses') if 'addresses' in data else []
            subgroups = data.pop('sub_groups') if 'sub_groups' in data else []
            c = Contact.query.filter_by(id=data['id']).first()

            if not c:
                raise GraphQLError('Invalid id (%s)' % data['id'])

            for k, v in data.items():
                setattr(c, k, v)

            if addresses:
                c.addresses = [Address(**address) for address in addresses]
            if subgroups:
                c.subgroups = [Subgroup(groupname=subgroup) for subgroup in subgroups]
            db.session.add(c)
        try:
            db.session.commit()
            return cls(ok=True, ids=[record['id'] for record in records])
        except Exception as e:
            raise GraphQLError(e.args)


class DeleteContacts(graphene.Mutation):
    class Arguments:
        """
            Mutation Arguments        
        """
        uids = graphene.List(graphene.String, required=True)

    ok = graphene.Boolean()

    @classmethod
    def mutate(cls, root, context, **kwargs):
        """ 
        Mutation logic is handled here
        """

        # More details about synchronize_session options in SqlAlchemy
        # http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.delete

        query = Contact.query.filter(
            Contact.id.in_(kwargs.get('uids', [])))

        objs = []

        for obj in query:
            db.session.delete(obj)
            objs.append(obj)

        db.session.info['changes'] = {'created': [], 'updated': [], 'deleted': objs}
        try:
            db.session.commit()
            return cls(ok=True)

        except Exception as e:
            raise GraphQLError(e.args)


class ContactMutation(BaseMutation):
    """
    Put all contact mutations here
    """
    create_contacts = CreateContacts.Field()
    delete_contacts = DeleteContacts.Field()
    update_contacts = UpdateContacts.Field()
