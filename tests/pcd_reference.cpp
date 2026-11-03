#include <pcl/io/pcd_io.h>
#include <pcl/PCLPointCloud2.h>
#include <Eigen/Geometry>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <limits>

int main(int argc, char **argv) {
    if (argc != 3) {
        std::cerr << "usage: pcd_reference input.pcd output.pcd\n";
        return 2;
    }
    pcl::PCLPointCloud2 cloud;
    Eigen::Vector4f origin;
    Eigen::Quaternionf orientation;
    int version;
    pcl::PCDReader reader;
    if (reader.read(argv[1], cloud, origin, orientation, version) < 0)
        return 1;
    pcl::PCDWriter writer;
    if (writer.writeBinary(argv[2], cloud, origin, orientation) < 0)
        return 1;
    std::cout << static_cast<uint64_t>(cloud.width) * cloud.height
              << " points, " << cloud.point_step << " bytes/point\n";
    for (const auto &field : cloud.fields) {
        if (field.datatype != pcl::PCLPointField::FLOAT32 || field.count != 1)
            continue;
        float minimum = std::numeric_limits<float>::infinity();
        float maximum = -minimum;
        uint64_t finite = 0;
        for (size_t i = 0; i < static_cast<size_t>(cloud.width) * cloud.height; ++i) {
            float value;
            std::memcpy(&value, cloud.data.data() + i * cloud.point_step + field.offset, 4);
            if (std::isfinite(value)) {
                minimum = std::min(minimum, value);
                maximum = std::max(maximum, value);
                ++finite;
            }
        }
        std::cout << std::setprecision(9) << field.name << ": min=" << minimum
                  << ", max=" << maximum << ", finite=" << finite << "\n";
    }
    return 0;
}
