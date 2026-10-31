#include <atomic>
#include <span>
#include <thread>
#include <kccachedb.h>

int main() {
    std::atomic<unsigned long long> count{0};
    std::thread worker([&] { ++count; });
    worker.join();
    int values[] = {1, 2};
    std::span<int> view(values);
    kyotocabinet::CacheDB db;
    std::string value;
    return !(count == 1 && view.size() == 2 &&
             db.open("*", kyotocabinet::CacheDB::OWRITER | kyotocabinet::CacheDB::OCREATE) &&
             db.set("key", "value") && db.get("key", &value) && value == "value" && db.close());
}
