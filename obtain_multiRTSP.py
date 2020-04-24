import cv2
import time
from queue import Queue
import threading
import numpy as np

rtsp1 = "rtsp://192.168.0.88/av0_0"
rtsp2 = "rtsp://192.168.0.89/av0_0"
rtsp3 = "rtsp://192.168.0.91/av0_0"
rtsp4 = "rtsp://192.168.0.90/av0_0"
cap1 = cv2.VideoCapture(rtsp1)
cap2 = cv2.VideoCapture(rtsp2)
cap3 = cv2.VideoCapture(rtsp3)
cap4 = cv2.VideoCapture(rtsp4)
# 初始化四个队列，设置大小以控制内存
q1 = Queue(maxsize=1)
q2 = Queue(maxsize=1)
q3 = Queue(maxsize=1)
q4 = Queue(maxsize=1)


def synchro_time(q):
    # 同步四个摄像头的时间
    # 思想是丢弃比其他摄像多的帧，确保每个摄像头都是最新帧
    latest = min(q1.qsize(), q2.qsize(), q3.qsize(), q4.qsize())
    if latest and q.qsize() > latest:
        for _ in range(q.qsize() - latest):
            q.get()


def get_frame(q, cap):
    while True:
        ret, frame = cap.read()
        if ret:
            synchro_time(q)
            if q == q1:
                frame = frame
            if q == q2:
                frame = frame
            if q == q3:
                frame = frame
            if q == q4:
                frame = frame
            latest = min(q1.qsize(), q2.qsize(), q3.qsize(), q4.qsize())
            # 当摄像头帧率不对等时，只能是最小的队列可以添加图片
            # 如果没有设置判断，队列会出现阻塞，直到队列为空才添加，这样的话，四帧图片的时间可能是对应不上的
            if q.qsize() == latest:
                q.put(frame)


h = 3000
w = 4000
c = 3
# 初始化一个占位空间
image = np.zeros([h * 2, w * 2, c], np.uint8)


def fill_frame(frame, pos):
    offset_y, offset_x, c = frame.shape
    if pos == "leftUp":
        image[:offset_y, :offset_x] = frame
        return True
    if pos == "rightUp":
        image[:offset_y, offset_x:] = frame
        return True
    if pos == "leftDown":
        image[offset_y:, :offset_x] = frame
        return True
    if pos == "rightDown":
        image[offset_y:, offset_x:] = frame
        return True
    return False

# 四个独立的线程分别启动视频流，同时完成了同步
t1 = threading.Thread(target=get_frame, args=(q1, cap1)).start()
t2 = threading.Thread(target=get_frame, args=(q2, cap2)).start()
t3 = threading.Thread(target=get_frame, args=(q3, cap3)).start()
t4 = threading.Thread(target=get_frame, args=(q4, cap4)).start()

from concurrent import futures

def threading_fill_frame():
    # 创建四个线程池，同时给占位图片的对应位置赋值
    with futures.ThreadPoolExecutor(4) as executor:
        res = executor.map(fill_frame, [q1.get(), q2.get(), q3.get(), q4.get()],
                           ['leftUp', 'rightUp', 'leftDown', 'rightDown'])
        if all(res):
            return True
        else:
            return False
# 主线程预览视频
def show():
    global image
    while True:
        image = np.zeros([h * 2, w * 2, c], np.uint8)
        if not q1.empty() and not q2.empty() and not q3.empty() and not q4.empty():
            start = time.time()
            threading_fill_frame()
            end = time.time()
            print("threading_fill_frame time:", end - start)
            frame = cv2.resize(image, (0, 0), fx=0.2, fy=0.2)
            cv2.imshow("frame", frame)
            if cv2.waitKey(1) & 0xff == ord('q'):
                break
	# 释放相机操作手柄与窗口
    cap1.release()
    cap2.release()
    cap3.release()
    cap4.release()
    cv2.destroyAllWindows()


show()
