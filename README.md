# Reverse Rate Limiter

***Simple reverse API rate limiting utility.***

> TL;DR: this medium article is a tutorial to get you fully implemented in under 10 minutes.

A reverse rate limiter is a mechanism that **limits the number of requests that can be made by a client over a given period of time**, in the opposite direction of a traditional rate limiter.

In a traditional rate limiter, the server limits the number of requests that a client can make over a given period of time in order to prevent the client from overwhelming the server with too many requests. A reverse rate limiter operates in the opposite direction, by limiting the number of requests that the client can send to a server over a given period of time. This can be useful for preventing servers from making too many requests to a server, hitting API rate limits and potentially overwhelming or slowing down the server.

Reverse rate limiters can be implemented in a variety of ways, such as by using token buckets or leaky buckets, or by using a sliding window approach. The presented implementation uses the sliding windows algorithm.

The sliding window approach is to maintain a window of time over which requests are counted, and to enforce a maximum number of requests that can be made within that window. For example, you could maintain a window of one minute, and allow a maximum of 100 requests to be made within that window.

## Context

In serverless computing, it is important to be able to coordinate services that do not communicate with each other as part of the scaling strategy in order to avoid making too many requests or hitting rate limits to external APIs.

Serverless computing allows for the creation of highly scalable, event-driven applications that can handle a large number of requests without the need to provision or manage servers. However, this scalability can also introduce challenges when it comes to communicating with external APIs, which may have rate limits in place to protect against excessive requests. These rate limits are defined per object (e.g. 5 request per second per account). The need for coordination appears when several uncoordinated services query in parallel a limited API in the name of the same account, consuming each part of the same quota limits. Hitting the quota limits is a risk, especially in the context of serverless applications.

Overall, being able to coordinate services in a serverless application is important for avoiding issues related to rate limits and ensuring that the application can scale effectively.

### As a reverse rate limiter

To avoid hitting external API rate limits, it is important to be able to coordinate the services within a serverless application so that they do not make too many requests to the external API in parallel. This can be done in a number of ways, such as by using a reverse rate limiter to limit the number of requests that a service can make to the API over a given period of time.

This utility proposes an ultra-lightweight implementation of a reverse rate limiter based on a redis database. This implementation is simple to get started with, robust for use in production and especially suited for serverless applications.

### As a classic rate limiter when no load balancer or gateway is present

A reverse rate limiter utility can also be used as a normal API rate limiter in situations where there is no load balancer or gateway are present, for example in serverless AWS lambda functions or containerized services such as Google Cloud Run.

In a typical API rate limiting scenario, a load balancer is used to distribute incoming requests across a pool of servers, and the rate limiter is implemented on the server side to limit the number of requests that each server can process over a given period of time. In this case, the rate limiter is protecting the servers from being overwhelmed by too many requests.

However, if there is no load balancer present, the rate limiter can still be used to limit the number of requests that are processed by the server. Managed services such as AWS lambda functions or Google cloud run do not provide easy access/setup of load balancer over the serverless app. In this case, the rate limiter would be protecting the server from being overwhelmed by too many requests from a single client by dropping the request and returning an error to the client before any further processing is made. This can be useful in situations where the server is not able to handle a large number of requests from a single client, concurrency design limitations, or where it is important to limit the number of requests that a client can make in order to protect the server's resources or respect a pricing policy. It makes a lot of sense to use this utility to limit service usage per user or per workspace depending on the pricing for instance.

Overall, a reverse rate limiter utility can be used in either a traditional rate limiting scenario, with a load balancer present to implement further business logic, or in a situation where there is no load balancer and the rate limiter is protecting a single server from being overwhelmed by too many requests from a single client.

## Description

The goal of this implementation is to be robust, ultra-lightweight and simple to get started within minutes. It is specifically designed for serverless functions or containerized serverless microservices featuring traffic bursts and ultra-scalability.

The rate limiting utility is build on top of the redis database.

It uses only the redis and time python libraries. The single implementation file can be copied directly to the codebase. This is done to ensure the best performance and avoid intermediaries and network latentency.

## Usage

The file `reverse_api_rate_limiter.py` is the main file you need to copy to your codebase. It includes the `ReverseRateLimiter`, the only class you need to instantiate to get started.

The file rate_testing.py is a testing file, to instantiate the `ReverseRateLimiter` and showcase how to use the utility in practice.

```python
from reverse_api_rate_limiter import ReverseRateLimiter

# instantiate the ReverseRateLimiter class
reverse_rate_limiter = ReverseRateLimiter(
    host = 'eu2-immense-elephant-30534.upstash.io',
    port = 30534,
    password = '*******')
```

Where you need to make an action that requires a credit from consuming towards to the rate limit you can use the two following options.

#### Option 1: request a credit, returns the number of credits left in the time window after the requested credit has been consumed.

This example is a rate of 5 requests per second maximum.

```python
# request a credit and get the remaining number of credits (after the requested credit has been consumed)
remaining_credits = reverse_rate_limiter.request_api_request_credit(
    key = 'user_id',
    window_in_seconds = 1,
    limit_per_window = 5)

# if the remaining_credits >= 0, a credit has been granted and consumed. 
# A request can be made immediately.
# if remaining_credits = -1, no credit has been granted nor consumed. 
# No request can be made. You can typically retry a credit request or have a custom fail logic.

# print the number of credits left in the time window
print(remaining_credits)
```

#### Option 2: request a credit, returns true/false if a credit has been granted and consumed. Keeps retrying at custom time intervals until it effectively gets a credit.

This example is a rate of 100 requests per 10 seconds. If the credits is not granted at the first request, it will automatically retry to request a credit 2 time at intervals of 0.1 second. The function will return `true` as soon as a credit is granted (and consumed). It returns `false` if none of the 3 requests (1 initial request and 2 retries) were granted a credit.

```python
# request a credit in a loop and print if the credit is granted each time (will print true or false)
for i in range(100):
    credit_is_granted = reverse_rate_limiter.get_api_request_credit(
        key = 'user_id',
        window_in_seconds = 10,
        limit_per_window = 100,
        wait_seconds_if_credit_not_granted=0.1,
        max_retries=2
        )
  
    print(credit_is_granted)
```


For more information on how to get started in less than 10 minutes, check out the medium article mentionned at the top of the readme.


© Full copyrights to Ruben Burdin, 2022
