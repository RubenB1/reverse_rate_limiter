from reverse_api_rate_limiter import ReverseRateLimiter

# instantiate the ReverseRateLimiter class
reverse_rate_limiter = ReverseRateLimiter(
    host = 'eu2-immense-elephant-30534.upstash.io',
    port = 30534,
    password = '*******')

## Simulate a setup where the rate limit is 5 requests per second per key.
# define the key
key = 'test_key'

# define the window in seconds
window_in_seconds = 1

# define the rate limit per window
limit_per_window = 5

# # request a credit in a loop and print if the credit is granted each time (will print true or false)
# for i in range(100):
#     credit_is_granted = reverse_rate_limiter.get_api_request_credit(
#         key = key,
#         window_in_seconds = window_in_seconds,
#         limit_per_window = limit_per_window
#         #wait_seconds_if_credit_not_granted=0.1
#         )
#     
#     print(credit_is_granted)

# request a credit in a loop and print if the credit is granted each time
for i in range(100):
    remaining_credits = reverse_rate_limiter.request_api_request_credit(
        key = key,
        window_in_seconds = window_in_seconds,
        limit_per_window = limit_per_window)
    
    # print the number of credits left in the time window
    print(remaining_credits)
    
    # if remaining_credits >= 0:
    #     print(True, remaining_credits)
    # else:
    #     print(False, remaining_credits)

