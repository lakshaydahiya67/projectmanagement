from rest_framework import serializers
from .models import Label, Task, Comment, Attachment
from users.serializers import UserSerializer

class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ['id', 'name', 'color', 'project']
        read_only_fields = ['project']

class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = Attachment
        fields = ['id', 'task', 'file', 'filename', 'uploaded_by', 'uploaded_by_name', 'uploaded_at', 'file_size']
        read_only_fields = ['uploaded_by', 'uploaded_at', 'file_size', 'filename']
    
    def create(self, validated_data):
        user = self.context['request'].user
        file = validated_data.get('file')
        validated_data['uploaded_by'] = user
        validated_data['filename'] = file.name
        validated_data['file_size'] = file.size
        return super().create(validated_data)

class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_picture = serializers.ImageField(source='author.profile_picture', read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'task', 'author', 'author_name', 'author_picture', 'content', 
                  'created_at', 'updated_at', 'parent', 'replies']
        read_only_fields = ['author', 'created_at', 'updated_at']
    
    def get_replies(self, obj):
        if obj.parent is None:  # Only get replies for top-level comments
            replies = Comment.objects.filter(parent=obj)
            return CommentSerializer(replies, many=True).data
        return []
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['author'] = user
        return super().create(validated_data)

class TaskSerializer(serializers.ModelSerializer):
    labels = LabelSerializer(many=True, read_only=True)
    assignees = UserSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    column_name = serializers.CharField(source='column.name', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'column', 'column_name', 'order',
            'created_by', 'created_by_name', 'created_at', 'updated_at', 
            'due_date', 'priority', 'priority_display', 'labels',
            'assignees', 'estimated_hours', 'actual_hours', 'is_overdue'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'is_overdue']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        
        # Set order to be the last in the column
        column = validated_data.get('column')
        latest_task = Task.objects.filter(column=column).order_by('-order').first()
        validated_data['order'] = (latest_task.order + 1) if latest_task else 0
        
        return super().create(validated_data)

class TaskDetailSerializer(TaskSerializer):
    comments = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True, read_only=True)
    
    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ['comments', 'attachments']
    
    def get_comments(self, obj):
        # Only get top-level comments (no parent)
        comments = Comment.objects.filter(task=obj, parent=None)
        return CommentSerializer(comments, many=True).data

class TaskMoveSerializer(serializers.Serializer):
    column = serializers.IntegerField()
    order = serializers.IntegerField()

class TaskAssignSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )
