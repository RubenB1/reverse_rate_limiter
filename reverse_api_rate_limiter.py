import redis
import time

class ReverseRateLimiter():
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        
        # connect to redis database
        self.r = redis.Redis(
            host = self.host,
            port = self.port,
            password = self.password,
            ssl = True,
            ssl_cert_reqs = u'none' #this line is needed to avoid error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate in certificate chain (_ssl.c:1125).
            )


    # execute the script with parameters
    def request_api_request_credit(self, key: str, window_in_seconds: int, limit_per_window: int) -> int:
        """
        Utility to request a credit to make an API request to redis.

        :param key: string, is the key for the sliding window
        :param window_in_seconds: int, is the length of the sliding window in seconds
        :param limit_per_window: int, is the maximum allowed number of credits per time window

        :return: int, is the number of credits left in the window
        """

        # Set lua script for sliding window algorithm
        # Since the script is executed in directly Redis, 
        # the script is executed in a single transaction.
        # from https://engagor.github.io/blog/2018/09/11/error-internal-rate-limit-reached/
        script = """
            local token = KEYS[1]
            local now = tonumber(ARGV[1])
            local window = tonumber(ARGV[2])
            local limit = tonumber(ARGV[3])

            local clearBefore = now - window * 1000000
            redis.call('ZREMRANGEBYSCORE', token, 0, clearBefore)

            local amount = redis.call('ZCARD', token)
            if amount < limit then
                redis.call('ZADD', token, now, now)
            end
            redis.call('EXPIRE', token, window)

            return limit - amount - 1
            """
        # Script limitations: a unique token is stored at the microsecond precision.
        # Since the list in redis is made of unique elements, 
        # adding twice the same element will not add a new element 
        # but simply replace the previous one. 
        # Thus, if two requests are made at the same microsecond,
        # both of them will consume a single API credit (risking to 
        # overpass the overall API threshold). If additonal precision is needed,
        # nanosecond precision can be used. This will however increase the
        # database storage and network load (drawback).
        # Microsecond precision is recommended for most use cases.

        # the current time in microseconds (now)
        current_time_microseconds = int(time.time() * 1000000)

        return self.r.eval(script, 1, key, current_time_microseconds, window_in_seconds, limit_per_window)
        # returns the number of request credits left in the window for that key
        # value >= 0, value is the number of credits left in the time window. A request credit has been granted to the current call.
        # value = -1, value is the number of credits left in the time window. The request credit has been DENIED to the current call.

    # get the authorization to make a request
    def get_api_request_credit(self, key: str, window_in_seconds: int, limit_per_window: int, wait_seconds_if_credit_not_granted: float = 0, max_retries: int = None) -> bool:
        """
        Request a credit to make an API request.

        :param key: string, is the key for the sliding window
        :param window_in_seconds: int, is the length of the sliding window in seconds
        :param limit_per_window: int, is the maximum number of credits per time window
        :param wait_seconds_if_credit_not_granted: float, is the number of seconds to wait if the credit is not granted before retry. 
        Default is 0 (do no wait and return false if the no credit is available in time window).
        If wait_seconds_if_credit_not_granted > 0, the function will wait and retry at given time intervals until the credit is granted.
        :param max_retries: int, is the maximum number of retries if the credit is not granted. Default is None (no limit, keeps retrying indefinitely).

        :return: bool, is the credit granted
        """

        number_of_credits_left_in_window = self.request_api_request_credit(key, window_in_seconds, limit_per_window)
        
        # if the credit is granted, return true.
        if number_of_credits_left_in_window >= 0:

            return True
        
        # if the credit is not granted, check the wait parameter
        elif wait_seconds_if_credit_not_granted > 0:
            # if the credit is not granted and wait parameter != 0, wait and retry 
            # in a loop at the given time intervals until the credit is granted
            # or the maximum number of retries is reached.
            number_of_trials = 0

            while number_of_credits_left_in_window < 0 and (max_retries is None or number_of_trials <= max_retries):
                time.sleep(wait_seconds_if_credit_not_granted)
                number_of_credits_left_in_window = self.request_api_request_credit(key, window_in_seconds, limit_per_window)

                if number_of_credits_left_in_window >= 0:
                    # if the credit is granted return true
                    return True
                    
                number_of_trials += 1

            # if the while loop is exited, the credit is not granted 
            # and the maximum number of retries is reached. Return false.
            return False

        else:
            # if the credit is not granted and wait parameter == 0, return false
            return False