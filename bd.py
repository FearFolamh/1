import psycopg2
from psycopg2.sql import NULL

host = "pg-281be636-ira-c799.b.aivencloud.com"  # Адрес хоста
database = "permission_bot"  # Название бд
user = "avnadmin"  # Юзер
password = "AVNS_8FYXXRmJKMIdVInjzQ7"  # Пароль
port = 14382


class PermissionDatabase:

    @staticmethod
    def _connect():
        try:
            connection = psycopg2.connect(host=host,
                                          database=database,
                                          port=port,
                                          user=user,
                                          password=password)
            cursor = connection.cursor()
            return connection, cursor
        except Exception as e:
            print(f"Exception due to executing connect: {e}")
            return None, None

    @staticmethod
    def _close_connection(connection=None, cursor=None):
        if connection and cursor:
            cursor.close()
            connection.close()

    def set_welcome_thread_message(self, thread_id):
        connection, cursor = self._connect()

        insert_query = """
            UPDATE public.config SET welcome_thread_id=%s WHERE id=%s;
        """
        data_to_insert = (thread_id, 1)
        try:
            cursor.execute(insert_query, data_to_insert)
            connection.commit()
            print(f"Welcome_thread_id was added to BD. {thread_id}")

        except Exception as e:
            print(
                f"Exception due to executing set_welcome_thread_message: {e}")
        finally:
            self._close_connection(connection, cursor)

    def set_group_id(self, chat_id):
        connection, cursor = self._connect()
        insert_query = """
            UPDATE public.config SET chat_id=%s WHERE id=%s;
        """
        data_to_insert = (chat_id, 1)
        try:
            cursor.execute(insert_query, data_to_insert)
            connection.commit()
            print(f"Chat_id was added to BD. {chat_id}")
        except Exception as e:
            print(f"Exception due to executing set_group_id: {e}")
        finally:
            self._close_connection(connection, cursor)

    def get_welcome_thread_message(self):
        connection, cursor = self._connect()

        select_query = """
            SELECT welcome_thread_id FROM config WHERE id=%s;
        """
        data_to_select = (1, )
        try:
            cursor.execute(select_query, data_to_select)
            result = cursor.fetchone()
            if result is None:
                print("No welcome_thread_id found in the database.")
                return None  # Или верните какое-то значение по умолчанию
            thread_id = result[0]
            print(f"Welcome_thread_id was fetched from BD: {thread_id}")
            return thread_id

            #cursor.execute(select_query, data_to_select)
            #thread_id = cursor.fetchone()[0]
            #print(f"Welcome_thread_id was fetched from BD. {thread_id}")

        except Exception as e:
            print(
                f"Exception due to executing get_welcome_thread_message: {e}")
        finally:
            self._close_connection(connection, cursor)

    def get_group_id(self):
        connection, cursor = self._connect()
        if (any([cursor, connection]) == NULL):
            return False

        select_query = """
            SELECT chat_id FROM config WHERE id=%s;
        """
        data_to_select = (1, )
        try:
            cursor.execute(select_query, data_to_select)
            chat_id = cursor.fetchone()
            if chat_id is None:
                print("No group_id found in the database.")
                return None
            print(f"Chat_id was fetched from BD. {chat_id}")
            return chat_id
        except Exception as e:
            print(f"Exception due to executing get_group_id: {e}")
        finally:
            self._close_connection(connection, cursor)

    def get_all_users(self):
        connection, cursor = self._connect()

        select_query = """
            SELECT user_id, position FROM users WHERE is_admin=False;
        """
        try:
            cursor.execute(select_query, )
            users = cursor.fetchall()
            print(f"Users was fetched from BD. {users}")
            return users
        except Exception as e:
            print(f"Exception due to executing get_all_users: {e}")
        finally:
            self._close_connection(connection, cursor)

    def update_users(self, members):
        connection, cursor = self._connect()
        user_id = None
        try:
            for member in members:
                user_id = member['user_id']
                name = member['name']
                username = member.get('username', None)
                position = member.get('position', None)

                query = """
                INSERT INTO users (user_id, name, username, position)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET position = EXCLUDED.position
                WHERE users.position <> EXCLUDED.position OR users.position IS NULL;
                """
                cursor.execute(query, (user_id, name, username, position))

                connection.commit()
                print(f"User with id={user_id} info was added/updated on BD.")
        except Exception as e:
            print(
                f"Exception due to executing update_users on user_id={user_id}: {e}"
            )
        finally:
            self._close_connection(connection, cursor)
