#there is no neen in this code anymore
#SKIP

# from django.db import connection

# def raw_likes_into_dislikes(disliked_playlist, disliked_video, liked_playlist):
#     with connection.cursor() as cursor:
#         cursor.execute("""
#             INSERT OR IGNORE 
#             INTO "macavity_playlist_included_video" ("playlist_id", "video_id") 
#             VALUES (%s, %s)""",[disliked_playlist, disliked_video])
#         cursor.execute("""DELETE FROM "macavity_playlist_included_video"
#             WHERE ("macavity_playlist_included_video"."playlist_id" = %s
#             AND "macavity_playlist_included_video"."video_id" IN (%s)) 
#         """, [liked_playlist, disliked_video])

# def raw_dislikes_into_likes(disliked_playlist, liked_video, liked_playlist):
#     with connection.cursor() as cursor:
#         cursor.execute("""
#             INSERT OR IGNORE 
#             INTO "macavity_playlist_included_video" ("playlist_id", "video_id") 
#             VALUES (%s, %s)""",
#             [liked_playlist, liked_video])
        
#         cursor.execute("""
#             DELETE FROM "macavity_playlist_included_video"
#             WHERE ("macavity_playlist_included_video"."playlist_id" = %s
#             AND "macavity_playlist_included_video"."video_id" IN (%s)) 
#             """,
#             [disliked_playlist, liked_video])


# def subscribe(subscriber_id, subscribed_at_id):
#     with connection.cursor() as cursor:
#         cursor.execute("""
#             INSERT OR IGNORE 
#             INTO "macavity_channel_sub_system" ("from_channel_id", "to_channel_id") 
#             VALUES (%s, %s)""",
#             [subscribed_at_id, subscriber_id])
        
# def get_number_of_subs(channel_id):
#     with connection.cursor() as cursor:
#         cursor.execute("""
#             SELECT COUNT("to_channel_id")
#             FROM "macavity_channel_sub_system"
#             WHERE ("from_channel_id" = %s)
#             """,
#             [channel_id])
#         sub_num = cursor.fetchone()[0]
#     return sub_num

# def get_channels_subscribed_at(channel_id):
#     with connection.cursor() as cursor:
#         cursor.execute("""
#             SELECT "from_channel_id" 
#             FROM "macavity_channel_sub_system" 
#             WHERE ("to_channel_id" = %s)
#             """,
#             [channel_id])
#         channels_tuples = cursor.fetchall()
#         channels = [tuple[0] for tuple in channels_tuples]
#     return channels

# def remove_subscription(subscriber_id, subscribed_at_id):
#     with connection.cursor() as cursor:
#         cursor.execute("""
#             DELETE 
#             FROM "macavity_channel_sub_system" 
#             WHERE ("from_channel_id" = %s
#             AND "to_channel_id" = %s)
#             """,
#             [subscribed_at_id, subscriber_id])

# def remove_all_subscriptions(channel_id):
#     with connection.cursor() as cursor:
#         cursor.execute("""
#             DELETE 
#             FROM "macavity_channel_sub_system" 
#             WHERE ("from_channel_id" = %s
#             OR "to_channel_id" = %s)
#             """, 
#             [channel_id, channel_id])

# def check_if_subscribed(subscriber_id, subscribed_at_id):
#     with connection.cursor() as cursor:
#         cursor.execute("""
#             SELECT *
#             FROM "macavity_channel_sub_system" 
#             WHERE ("from_channel_id" = %s
#             AND "to_channel_id" = %s)
#             """, 
#             [subscribed_at_id, subscriber_id])
#         subscribed = cursor.fetchone()
#     if subscribed is None:
#         return False
#     else:
#         return True
