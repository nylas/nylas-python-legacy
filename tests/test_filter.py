import json
import random
import responses
from urlobject import URLObject


def test_no_filter(mocked_responses, api_client, api_url, message_body):
    message_body_list_50 = [message_body for _ in range(1, 51)]
    message_body_list_22 = [message_body for _ in range(1, 23)]

    values = [
        (200, {}, json.dumps(message_body_list_22)),
        (200, {}, json.dumps(message_body_list_50)),
    ]

    def callback(request):
        return values.pop()

    mocked_responses.add_callback(
        responses.GET,
        api_url + '/events',
        callback=callback,
    )

    events = api_client.events.all()
    assert len(events) == 72
    assert events[0].id == 'cv4ei7syx10uvsxbs21ccsezf'


def test_two_filters(mocked_responses, api_client, api_url):
    mocked_responses.add(
        responses.GET,
        api_url + '/events?param1=a&param2=b',
        body='[]',
    )
    events = api_client.events.where(param1='a', param2='b').all()
    assert len(events) == 0  # pylint: disable=len-as-condition
    url = mocked_responses.calls[-1].request.url
    query = URLObject(url).query_dict
    assert query['param1'] == 'a'
    assert query['param2'] == 'b'

def test_no_offset(mocked_responses, api_client, api_url):
    mocked_responses.add(
        responses.GET,
        api_url + '/events?in=Nylas',
        body='[]',
    )
    list(api_client.events.where({'in': 'Nylas'}).items())
    url = mocked_responses.calls[-1].request.url
    query = URLObject(url).query_dict
    assert query['in'] == 'Nylas'
    assert query['offset'] == '0'

def test_zero_offset(mocked_responses, api_client, api_url):
    mocked_responses.add(
        responses.GET,
        api_url + '/events?in=Nylas&offset=0',
        body='[]',
    )
    list(api_client.events.where({'in': 'Nylas', 'offset': 0}).items())
    url = mocked_responses.calls[-1].request.url
    query = URLObject(url).query_dict
    assert query['in'] == 'Nylas'
    assert query['offset'] == '0'

def test_non_zero_offset(mocked_responses, api_client, api_url):
    offset = random.randint(1, 1000)
    mocked_responses.add(
        responses.GET,
        api_url + '/events?in=Nylas&offset=' + str(offset),
        body='[]',
    )

    list(api_client.events.where({'in': 'Nylas', 'offset': offset}).items())
    url = mocked_responses.calls[-1].request.url
    query = URLObject(url).query_dict
    assert query['in'] == 'Nylas'
    assert query['offset'] == str(offset)
