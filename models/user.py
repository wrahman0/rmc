import mongoengine as me

class User(me.Document):

    class JoinSource(object):
        FACEBOOK = 1

    meta = {
        'indexes': [
            'fb_access_token',
            'fbid',
        ],
    }

    # id = me.ObjectIdField(primary_key=True)

    # TODO(mack): join_date should be encapsulate in _id, but store it
    # for now, just in case; can remove it when sure that info is in _id
    join_date = me.DateTimeField(required=True)
    join_source = me.IntField(required=True, choices=[JoinSource.FACEBOOK])

    # eg. Mack
    first_name = me.StringField(required=True)

    middle_name = me.StringField()

    # eg. Duan
    last_name = me.StringField(required=True)

    # TODO(mack): check if facebook always returns gender field
    gender = me.StringField(choices=['male', 'female'])

    # eg. 1647810326
    fbid = me.StringField(required=True, unique=True)

    # http://stackoverflow.com/questions/4408945/what-is-the-length-of-the-access-token-in-facebook-oauth2
    fb_access_token = me.StringField(max_length=255, required=True, unique=True)
    fb_access_token_expiry_date = me.DateTimeField(required=True)

    email = me.EmailField()

    # eg. list of user objectids, could be friends from sources besides facebook
    friend_ids = me.ListField(me.ObjectIdField())
    # eg. list of fbids of friends from facebook, not necessarily all of whom
    # use the site
    friend_fbids = me.ListField(me.StringField())

    birth_date = me.DateTimeField()

    last_visited = me.DateTimeField()
    # TODO(mack): consider using SequenceField()
    num_visits = me.IntField(min_value=0, default=0)

    # eg. mduan or 20345619 ?
    student_id = me.StringField()
    # eg. university_of_waterloo ?
    school_id = me.StringField()
    # eg. software_engineering ?
    program_id = me.StringField()

    # List of UserCourse.id's
    course_history = me.ListField(me.ObjectIdField())

    @property
    def name(self):
        return '%s %s' % (self.first_name , self.last_name)

    def save(self, *args, **kwargs):

        # TODO(mack): If _changed_fields attribute does not exist, it mean
        # document has been saved yet. Just need to verify. In this case,
        # we could just check if id has been set
        first_save = not hasattr(self, '_changed_fields')

        if first_save:
            # TODO(Sandy): We're assuming people won't unfriend anyone.
            # Fix this later?

            # TODO(mack): this isn't safe against race condition of both
            # friends signing up at same time
            #print 'friend_fbids', self.friend_fbids
            friends = User.objects(fbid__in=self.friend_fbids).only('id', 'friend_ids')
            self.friend_ids = [f.id for f in friends]

        super(User, self).save(*args, **kwargs)

        if first_save:
            # TODO(mack): should do this asynchronously
            # Using update rather than save because it should be more efficient
            friends.update(add_to_set__friend_ids=self.id)

    @classmethod
    def cls_mutual_courses_redis_key(cls, user_id_one, user_id_two):
        if user_id_one < user_id_two:
            first_id = user_id_one
            second_id = user_id_two
        else:
            first_id = user_id_two
            second_id = user_id_one
        return 'mutual_courses:%s:%s' %  (first_id, second_id)

    def mutual_courses_redis_key(self, other_user_id):
        return User.cls_mutual_courses_redis_key(self.id, other_user_id)
