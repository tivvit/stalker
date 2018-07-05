from endomondo.endomondo import MobileApi
import config
import sys

if __name__ == '__main__':
    if not config.endomondo_username or not config.endomondo_pass:
        print("provide username and password first")
        sys.exit(1)

    print("User {}".format(config.endomondo_username))
    endomondo = MobileApi(email=config.endomondo_username,
                          password=config.endomondo_pass)

    auth_token = endomondo.get_auth_token()
    print(auth_token)
