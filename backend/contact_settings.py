import re
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator


class ContactSettings(BaseModel):
    contact_label: str = Field(default='Hubungi administrator SISDUR.', min_length=1, max_length=120)
    contact_url: str = Field(default='', max_length=2048)

    @field_validator('contact_label', mode='before')
    @classmethod
    def clean_label(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator('contact_url')
    @classmethod
    def validate_contact_url(cls, value):
        value = value.strip()
        if not value:
            return value
        message = 'Gunakan tautan https://, http://, mailto:email, atau tel:nomor yang valid.'
        if re.search(r'\s|[\\<>\x00-\x1f\x7f]', value) or re.search(r'%0[ad]', value, re.I):
            raise ValueError(message)
        try:
            parsed = urlsplit(value)
            if parsed.scheme in ('http', 'https'):
                if parsed.hostname and not parsed.username and not parsed.password and parsed.port != 0:
                    return value
            elif parsed.scheme == 'mailto' and not parsed.netloc and not parsed.fragment:
                if re.fullmatch(r'[^@/?]+@[^@/?]+\.[^@/?]+', parsed.path):
                    return value
            elif parsed.scheme == 'tel' and not parsed.netloc and not parsed.query and not parsed.fragment:
                if re.fullmatch(r'\+?[0-9().-]{3,30}', parsed.path):
                    return value
        except ValueError:
            pass
        raise ValueError(message)