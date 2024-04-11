import sys
from yandex_music import Client, Album
from bs4 import BeautifulSoup
import csv
import json

KEYS = ("id", "name", "presumptive_type", "genre", "count_child_element", "is_bookmate")


class CaptchaError(Exception):
    code = 429
    message = "Too many"


class EmptyError(Exception):
    code = 404
    message = "Empty response"


TOKEN = ""


def init_client(token):
    client = Client(token).init()
    return client


def get_request(client: Client, id_: int) -> Album | None:
    album = client.albums_with_tracks(id_)
    return album


def response_parse(response: str) -> tuple[str, dict[str, str]]:
    parsed_text = BeautifulSoup(response, "html.parser")
    light_data = parsed_text.findAll("script", class_="light-data")
    if not light_data:
        raise EmptyError
    content_data = json.loads(light_data[0].text)
    genre = content_data.get("genre", "any")
    tracks_count = len(content_data.get("track", []))
    numTracks = content_data.get("numTracks", 0)
    type_ = get_presumptive_type(genre, numTracks)
    result_content = {
        "name": content_data.get("name", "any"),
        "genre": genre,
        "presumptive_type": type_,
        "count_child_element": tracks_count,
    }
    return type_, result_content


def get_presumptive_type(genre: str, num_tracks: int) -> str:
    if genre == "podcasts":
        return "podcast"
    if num_tracks == 0:
        return "audiobook"
    return "any"


def is_bookmate(option: list[str | None] = None) -> bool:
    try:
        if option[0] == "bookmate":
            return True
    except Exception:
        return False


def get_track_count_for_audiobook(volumes: list[str | None] = None) -> int:
    result = 0
    try:
        result = len(volumes[0])
    except Exception:
        print(f"volumes error: {volumes}")
    return result


def get_data_from_album(album: Album) -> tuple[str, dict[str, str]]:
    content_data = album

    genre = album.meta_type
    type_ = album.type
    tracks_count = (
        content_data.track_count
        if content_data.track_count
        else get_track_count_for_audiobook(album.volumes)
    )
    result_content = {
        "id": album.id,
        "name": content_data.title,
        "genre": genre,
        "presumptive_type": type_,
        "count_child_element": tracks_count,
        "is_bookmate": is_bookmate(content_data.available_for_options),
    }
    return type_, result_content


def parsing_ym(start_item: int, end_item: int) -> None:
    result = []
    client = init_client(TOKEN)

    try:
        for id_ in range(start_item, end_item + 1):
            if id_ % 1000 == 0:
                print(id_)

            response = get_request(client, id_)
            if response.error:
                continue
            try:
                # genre, res = response_parse(response)
                genre, res = get_data_from_album(response)
            except EmptyError:
                # sleep(1)
                continue
            if genre not in ["audiobook", "podcast"]:
                # sleep(1)
                continue
            else:
                result.append(res)

    except (CaptchaError, TimeoutError, Exception) as exc:
        print(id_)
        print(f"Captcha error: {exc}")
    if result:
        write_result(result)
        print(f"Data was written to file, end_id={id_}")
    else:
        print(f"No data; end_id={id_}")


def write_result(result_list: list[dict[str, str]]) -> None:
    with open("yandex_parsing.csv", "a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=KEYS)
        # writer.writeheader()
        writer.writerows(result_list)


if __name__ == "__main__":
    start_item = int(sys.argv[1])
    end_item = int(sys.argv[2])
    # end_item = start_item + 10
    parsing_ym(start_item, end_item)
