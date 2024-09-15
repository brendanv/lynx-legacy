import json
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.core import serializers
from lynx.models import Link, Tag, Note, Feed, FeedItem, LinkArchive

User = get_user_model()

class Command(BaseCommand):
    help = 'Exports all data for a given user in JSON format, excluding UserSettings'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user to export data for')

    def handle(self, *args, **options):
        username = options['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist')

        data = {}

        models_to_export = [
            Tag, Note, Feed, LinkArchive
        ]

        # Need to use the full content to get all the fields
        links_with_content = Link.objects_with_full_content.filter(user=user)
        data[Link.__name__] = json.loads(serializers.serialize('json', links_with_content))
        
        for model in models_to_export:
            queryset = model.objects.filter(user=user)
            data[model.__name__] = json.loads(serializers.serialize('json', queryset))

        # Feed Items don't have user directly on the model
        feed_items = FeedItem.objects.filter(feed__user=user)
        data[FeedItem.__name__] = json.loads(serializers.serialize('json', feed_items))
        
        output = json.dumps(data, indent=2)

        filename = f'{username}_data_export.json'
        with open(filename, 'w') as f:
            f.write(output)

        self.stdout.write(self.style.SUCCESS(f'Successfully exported data for user "{username}" to {filename}'))