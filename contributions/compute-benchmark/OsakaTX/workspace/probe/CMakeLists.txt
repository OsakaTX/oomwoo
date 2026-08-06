cmake_minimum_required(VERSION 3.8)
project(oomwoo_bench_probe)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

# --- composable component library ---
add_library(oomwoo_bench_fixture SHARED
  src/fixture_worker.cpp)
target_include_directories(oomwoo_bench_fixture PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
ament_target_dependencies(oomwoo_bench_fixture
  rclcpp rclcpp_components std_msgs)
rclcpp_components_register_node(oomwoo_bench_fixture
  PLUGIN "oomwoo_bench::FixtureWorker"
  EXECUTABLE fixture_worker)

# --- standalone worker executable (one process, N nodes via count param) ---
add_executable(bench_worker src/bench_worker_main.cpp)
target_include_directories(bench_worker PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/include)
ament_target_dependencies(bench_worker rclcpp)
target_link_libraries(bench_worker oomwoo_bench_fixture)

# --- odom/tf probe executable (slam_toolbox GetPoseHelper reproduction) ---
add_executable(odom_probe src/odom_probe.cpp)
ament_target_dependencies(odom_probe
  rclcpp rclcpp_components sensor_msgs geometry_msgs tf2_ros tf2_geometry_msgs)

install(TARGETS
  oomwoo_bench_fixture
  bench_worker
  odom_probe
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME}
  )

ament_export_dependencies(rclcpp rclcpp_components tf2_ros sensor_msgs std_msgs geometry_msgs)
ament_package()
