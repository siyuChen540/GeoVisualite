# 地理空间数据可视化工具 (NC/SHP)

[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-%232196F3.svg?style=flat&logo=PyQt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![NetCDF4](https://img.shields.io/badge/netCDF4-%232E8B57.svg?style=flat&logo=python&logoColor=white)](https://unidata.github.io/netcdf4-python/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-%23FF9800.svg?style=flat&logo=matplotlib&logoColor=white)](https://matplotlib.org/)
[![GeoPandas](https://img.shields.io/badge/GeoPandas-%235CB85C.svg?style=flat&logo=pandas&logoColor=white)](https://geopandas.org/)
[![Cartopy](https://img.shields.io/badge/Cartopy-%234682B4.svg?style=flat&logo=python&logoColor=white)](https://scitools.org.uk/cartopy/)
[![Qtawesome](https://img.shields.io/badge/Qtawesome-%23333.svg?style=flat&logo=font-awesome&logoColor=white)](https://pypi.org/project/QtAwesome/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**版本:** 3.6 (集成工具栏导航 & Bug 修复)
**日期:** 2025/06/23
**作者:** Siyu Chen
**邮箱:** chensy57@mail2.sysu.edu.cn
**许可证:** MIT License

## 简介

**地理空间数据可视化工具** 是一款功能强大的桌面应用程序，旨在帮助用户轻松查看和分析地理空间数据。它支持两种主要的地理数据格式：**NetCDF (.nc)** 和 **Shapefile (.shp)**。该工具采用现代化的用户界面，基于 **PyQt5** 框架开发，并利用 **Matplotlib**、**Geopandas** 和 **Cartopy** 等强大的 Python 库进行数据处理和可视化。

**主要特点:**

* **直观的用户界面:** 采用清晰的两栏布局，左侧面板用于文件管理和变量选择，右侧主区域通过选项卡显示文件元数据和交互式地图。
* **多格式支持:** 支持加载和查看 NetCDF (.nc) 文件和 Shapefile (.shp) 文件。
* **NetCDF 文件查看:**
    * 显示详细的全局属性、维度和变量信息。
    * 支持双击列表中的变量进行快速二维地图绘制。
    * 对于多维变量，提供灵活的维度选择对话框，允许用户选择坐标轴和用于导航/步进的维度。
* **Shapefile 文件查看:**
    * 显示 Shapefile 的基本信息，包括坐标参考系统 (CRS)、要素数量和几何类型。
    * 自动可视化 Shapefile 的地理要素。
* **集成工具栏导航:** 对于多维 NetCDF 变量，Matplotlib 工具栏集成了“上一个”和“下一个”按钮，方便用户按选定的导航维度浏览数据切片。同时显示当前导航维度和索引信息。
* **灵活的投影:** 使用 Cartopy 库进行地图绘制，支持多种地图投影，并自动添加海岸线和网格线。
* **颜色条:** 绘制的地图包含颜色条，清晰展示数据的数值范围。
* **文件加载方式多样:** 支持通过“打开文件”按钮选择文件，也支持直接将文件拖拽到程序窗口进行加载。
* **历史记录:** 记录最近打开的文件，方便快速访问。
* **现代 UI 风格:** 通过自定义 QSS 样式表 (style.qss) 提供美观且一致的用户体验（如果样式表文件存在）。
* **错误处理:** 提供清晰的错误消息提示，帮助用户诊断问题。

## 依赖

在使用此工具之前，请确保您的 Python 环境中已安装以下依赖库：

* **PyQt5:** 用于创建图形用户界面。
* **netCDF4:** 用于读取和处理 NetCDF 文件。
* **matplotlib:** 用于生成图表和地图。
* **geopandas:** 用于处理地理空间数据，特别是 Shapefile。
* **cartopy:** 用于地理空间数据的地图投影和绘制。
* **numpy:** 用于科学计算和数组操作。
* **qtawesome:** 用于添加图标，提升用户界面美观性。

您可以使用 pip 或 conda 来安装这些依赖：

**使用 pip:**

   ```bash
   pip install PyQt5 netCDF4 matplotlib geopandas cartopy numpy qtawesome
   ```

**使用 conda:**

   ```bash
   conda create -n geoDraw python=3.x
   conda activate geoDraw
   conda install -c conda-forge pyqt=5 netcdf4 matplotlib geopandas cartopy numpy qtawesome
   ```

## 如何使用
1. 克隆或下载 此代码库到您的本地计算机。

2. 安装依赖 (参见上面的“依赖”部分)。

3. 运行程序: 在命令行或终端中，导航到包含 main.py 文件的目录，并执行以下命令：
```bash
python main.py
```
4. 加载数据:

- 通过菜单: 点击程序左上角的“打开文件”按钮，选择您想要查看的 .nc 或 .shp 文件。
- 拖拽: 将 .nc 或 .shp 文件直接拖拽到程序窗口中。
- 查看文件元数据: 文件加载成功后，“文件元数据”选项卡将显示文件的详细信息。

5. 可视化数据:

- NetCDF: 在左侧面板的变量列表中，双击您想要绘制的二维变量。对于多维变量，将弹出一个“选择维度、坐标轴和导航轴”对话框，您需要选择用于 X 轴（通常是经度）、Y 轴（通常是纬度）的维度，以及用于在工具栏中导航的维度（可选）。选择完成后点击“确定”即可生成地图。使用工具栏中的“上一个”和“下一个”按钮可以浏览导航维度的不同切片。
- Shapefile: 文件加载后将自动在“数据可视化”选项卡中显示地理要素。
- 查看历史记录: 点击“显示历史”按钮可以查看最近打开的文件列表。点击“返回主界面”返回初始状态。

## 界面概览
- 左侧面板:
   - “打开文件”按钮: 用于选择并加载地理空间数据文件。
   - “显示历史”按钮: 用于查看最近打开的文件记录。
   - “返回主界面”按钮: 用于清空当前视图并返回初始欢迎界面。
   - 可绘制变量列表: 显示 NetCDF 文件中可以进行二维或高维可视化的变量。双击列表项进行绘图。
- 右侧主区域:
   - “文件元数据”选项卡: 显示加载的 NetCDF 或 Shapefile 的详细元数据信息。
   - “数据可视化”选项卡: 显示根据所选数据生成的交互式地图。该选项卡包含 Matplotlib 工具栏，对于多维 NetCDF 数据，工具栏中会显示导航控件。

## 许可证
本项目采用MIT许可证