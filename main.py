import requests
import json
import time

games_to_crawl = {
    "Baldurs_Gate_3": "1086940",
    "Elden_Ring": "1245620",
    "Solo_Leveling_Arise": "2373990", 
    "Monster_Hunter_Wilds": "2246340" 
}

TOTAL_TARGET = 25000
TARGET_PER_GAME = TOTAL_TARGET // len(games_to_crawl) + 1 

overall_reviews_collected = 0

print(f"==========================================")
print(f"총 목표 리뷰 수: {TOTAL_TARGET}개")
print(f"크롤링 대상 게임 수: {len(games_to_crawl)}개")
print(f"게임당 목표 리뷰 수: {TARGET_PER_GAME}개")
print(f"==========================================")


for game_name, app_id in games_to_crawl.items():

    print(f"\n==========================================")
    print(f"{game_name} ({app_id}) 크롤링 시작")
    print(f"목표 수량: {TARGET_PER_GAME}개 (현재까지 총 {overall_reviews_collected}개)")
    print(f"==========================================")

    url = f"https://store.steampowered.com/appreviews/{app_id}"
    params = {
        "json": 1,
        "language": "korean",
        "filter": "all",
        "num_per_page": 100,
        "cursor": "*"
    }

    all_reviews_for_game = []
    prev_cursor = None

    if overall_reviews_collected >= TOTAL_TARGET:
        print("전체 목표 수량 달성 크롤링을 종료합니다.")
        break

    while len(all_reviews_for_game) < TARGET_PER_GAME:
        
        if overall_reviews_collected >= TOTAL_TARGET:
            print("전체 목표 수량 달성 임박. 이 게임의 크롤링을 중단합니다.")
            break

        data = None
        for attempt in range(3):
            try:
                if not str(app_id).isdigit():
                      print(f" '{game_name}'의 App ID '{app_id}'가 유효하지 않아 스킵합니다.")
                      data = None
                      break

                response = requests.get(url, params=params, timeout=(10, 30))

                if response.status_code == 429:
                    print(" 429 에러 발생 (너무 많은 요청). 90초 대기 후 재시도...")
                    time.sleep(90)
                    continue
                
                if response.status_code != 200:
                    print(f" HTTP Error {response.status_code} 발생. 재시도...")
                    time.sleep(5)
                    continue
                
                data = response.json()
                break 

            except requests.exceptions.ConnectTimeout:
                print(f" 연결 타임아웃 발생 (시도 {attempt + 1}/3)... 5초 대기")
                time.sleep(5)
            except requests.exceptions.ReadTimeout:
                print(f" 응답 타임아웃 발생 (시도 {attempt + 1}/3)... 5초 대기")
                time.sleep(5)
            except requests.exceptions.RequestException as e:
                print(f" 기타 요청 오류 발생: {e}")
                break
            except json.JSONDecodeError:
                print(" JSON 디코딩 오류 발생 (응답이 JSON 형태가 아님).")
                break


        if data is None or 'reviews' not in data:
            print(f" {game_name}: 데이터 수신 실패 또는 리뷰 없음. 다음 게임으로 이동.")
            break

        if data.get("success") != 1:
            print(" 요청 실패 (API success=0).")
            break

        reviews = data.get("reviews", [])
        if not reviews:
            print(" 더 이상 가져올 리뷰가 없습니다. 이 게임 크롤링 종료.")
            break

        all_reviews_for_game.extend(reviews)
        overall_reviews_collected += len(reviews)
        
        current_game_count = len(all_reviews_for_game)
        progress_ratio = current_game_count / TARGET_PER_GAME
        
        print(f" {game_name} 수집 중: {current_game_count} / {TARGET_PER_GAME}개 ({progress_ratio:.1%}) | 총 {overall_reviews_collected}개")

        cursor = data.get("cursor")
        if not cursor or cursor == prev_cursor:
            print("커서 반복 또는 끝 도달. 이 게임 크롤링 종료.")
            break

        prev_cursor = cursor
        params["cursor"] = cursor

        time.sleep(5)

    filename = f"{game_name}_reviews.json"
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(all_reviews_for_game, json_file, ensure_ascii=False, indent=4)

    print(f" {game_name} 저장 완료 ({filename}) - 수집된 개수: {len(all_reviews_for_game)}")


print("\n\n 모든 게임 데이터 수집이 완료")