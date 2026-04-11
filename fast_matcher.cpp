/*
 * SportsGuard AI — Fast Matcher (Module B)
 * High-speed perceptual hash matching engine using Hamming distance.
 *
 * Compiled as a Python extension via pybind11.
 *
 * Build:
 *     python setup.py build_ext --inplace
 *
 * Usage from Python:
 *     import fast_matcher
 *     result = fast_matcher.find_best_match(query_hash, db_hashes, threshold=5)
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cstdint>
#include <vector>
#include <utility>
#include <limits>

#ifdef _MSC_VER
#include <intrin.h>
// MSVC does not have __builtin_popcountll; use __popcnt64 instead
static inline int popcount64(uint64_t x) {
    return static_cast<int>(__popcnt64(x));
}
#else
static inline int popcount64(uint64_t x) {
    return __builtin_popcountll(x);
}
#endif

namespace py = pybind11;

// ────────────────────────────────────────────────────────────────────────────
// Result struct returned to Python
// ────────────────────────────────────────────────────────────────────────────
struct MatchResult {
    int    video_id;          // -1 if no match
    double confidence;        // 0.0 – 100.0
    int    hamming_distance;  // 0 – 64
};

// ────────────────────────────────────────────────────────────────────────────
// Core matching function
// ────────────────────────────────────────────────────────────────────────────
MatchResult find_best_match(
    uint64_t query_hash,
    const std::vector<std::pair<uint64_t, int>>& db_hashes,
    int threshold = 5)
{
    int    best_distance = std::numeric_limits<int>::max();
    int    best_video_id = -1;
    size_t n             = db_hashes.size();

    // Thread-local reduction: each thread tracks its own best, merge once
    #pragma omp parallel
    {
        int local_best_dist = std::numeric_limits<int>::max();
        int local_best_vid  = -1;

        #pragma omp for schedule(static) nowait
        for (size_t i = 0; i < n; ++i) {
            int dist = popcount64(query_hash ^ db_hashes[i].first);
            if (dist < local_best_dist) {
                local_best_dist = dist;
                local_best_vid  = db_hashes[i].second;
            }
        }

        #pragma omp critical
        {
            if (local_best_dist < best_distance) {
                best_distance = local_best_dist;
                best_video_id = local_best_vid;
            }
        }
    }

    MatchResult result;

    if (best_distance <= threshold) {
        result.video_id         = best_video_id;
        result.hamming_distance = best_distance;
        result.confidence       = (64.0 - best_distance) / 64.0 * 100.0;
    } else {
        result.video_id         = -1;
        result.hamming_distance = best_distance;
        result.confidence       = 0.0;
    }

    return result;
}

// ────────────────────────────────────────────────────────────────────────────
// Batch matching: compare multiple query hashes against the database
// ────────────────────────────────────────────────────────────────────────────
std::vector<MatchResult> find_best_matches(
    const std::vector<uint64_t>& query_hashes,
    const std::vector<std::pair<uint64_t, int>>& db_hashes,
    int threshold = 5)
{
    std::vector<MatchResult> results;
    results.reserve(query_hashes.size());

    for (auto qh : query_hashes) {
        results.push_back(find_best_match(qh, db_hashes, threshold));
    }

    return results;
}

// ────────────────────────────────────────────────────────────────────────────
// pybind11 module definition
// ────────────────────────────────────────────────────────────────────────────
PYBIND11_MODULE(fast_matcher, m) {
    m.doc() = "SportsGuard AI — High-speed perceptual hash matching engine";

    // Expose MatchResult as a Python class
    py::class_<MatchResult>(m, "MatchResult")
        .def_readonly("video_id",         &MatchResult::video_id)
        .def_readonly("confidence",       &MatchResult::confidence)
        .def_readonly("hamming_distance", &MatchResult::hamming_distance)
        .def("__repr__", [](const MatchResult& r) {
            return "<MatchResult video_id=" + std::to_string(r.video_id) +
                   " confidence=" + std::to_string(r.confidence) +
                   "% hamming=" + std::to_string(r.hamming_distance) + ">";
        })
        .def("to_dict", [](const MatchResult& r) {
            py::dict d;
            d["video_id"]         = r.video_id;
            d["confidence"]       = r.confidence;
            d["hamming_distance"] = r.hamming_distance;
            return d;
        });

    // Expose single-query match function
    m.def("find_best_match", &find_best_match,
          py::arg("query_hash"),
          py::arg("db_hashes"),
          py::arg("threshold") = 5,
          R"doc(
Find the best matching video for a single query hash.

Parameters
----------
query_hash : int
    64-bit perceptual hash to search for.
db_hashes : list of (int, int)
    Database entries as (phash, video_id) pairs.
threshold : int, optional
    Maximum Hamming distance to accept (default 5).

Returns
-------
MatchResult
    Contains video_id (-1 if no match), confidence %, and hamming_distance.
)doc");

    // Expose batch match function
    m.def("find_best_matches", &find_best_matches,
          py::arg("query_hashes"),
          py::arg("db_hashes"),
          py::arg("threshold") = 5,
          R"doc(
Find the best matching video for each query hash in a batch.

Parameters
----------
query_hashes : list of int
    64-bit perceptual hashes to search for.
db_hashes : list of (int, int)
    Database entries as (phash, video_id) pairs.
threshold : int, optional
    Maximum Hamming distance to accept (default 5).

Returns
-------
list of MatchResult
)doc");
}
