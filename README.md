<a href="https://www.nylas.com/">
    <img src="https://brand.nylas.com/assets/downloads/logo_horizontal_png/Nylas-Logo-Horizontal-Blue_.png" alt="Aimeos logo" title="Aimeos" align="right" height="60" />
</a>

# Nylas Python SDK (Legacy/API v2)

This is the legacy version of the Nylas Python SDK, which supports the Nylas API v2. This version of the SDK is currently in maintenance mode and is supported for the purpose of assisting with migration to the new API v3. We recommend migrating and using the current [Nylas Python SDK](https://www.github.com/nylas/nylas-python) for the latest and greatest features.

## ⚙️ Install

The Nylas Python SDK is available via pip:

```bash
pip install nylas-legacy
```

To install the SDK from source, clone this repo and run the install script.

```bash
git clone https://github.com/nylas/nylas-python-legacy.git && cd nylas-python-legacy
python setup.py install
```

## ⚡️ Usage

To use this SDK, you first need to [sign up for a free Nylas developer account](https://nylas.com/register).

Then, follow our guide to [setup your first app and get your API access keys](https://docs.nylas.com/docs/get-your-developer-api-keys).

Next, in your python script, import the `APIClient` class from the `nylas` package, and create a new instance of this class, passing the variables you gathered when you got your developer API keys. In the following example, replace `CLIENT_ID`, `CLIENT_SECRET`, and `ACCESS_TOKEN` with your values.


```python
from nylas_legacy import APIClient

nylas = APIClient(
    CLIENT_ID,
    CLIENT_SECRET,
    ACCESS_TOKEN
)
```

Now, you can use `nylas` to access full email, calendar, and contacts functionality. For example, here is how you would print the subject line for the most recent email message to the console.


```python
message = nylas.messages.first()
print(message.subject)
```

To learn more about how to use the Nylas Python SDK, please refer to our [Python SDK QuickStart Guide](https://docs.nylas.com/docs/quickstart-python) and our [Python tutorials](https://docs.nylas.com/docs/tutorials).

## 💙 Contributing

Please refer to [Contributing](Contributing.md) for information about how to make contributions to this project. We welcome questions, bug reports, and pull requests.

## 📝 License

This project is licensed under the terms of the MIT license. Please refer to [LICENSE](LICENSE) for the full terms.
