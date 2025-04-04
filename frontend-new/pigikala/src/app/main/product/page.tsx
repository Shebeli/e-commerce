"use client";

import {
  colors,
  details,
  images,
} from "@/app/ui/product-page/placeholder-data";
import ProductColor from "@/app/ui/product-page/product-color";
import ProductDetail from "@/app/ui/product-page/product-detail";
import ProductFeature from "@/app/ui/product-page/product-feature";
import ProductImage from "@/app/ui/product-page/product-image";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import {
  FaCalendarCheck,
  FaCheck,
  FaCreditCard,
  FaHeadset,
  FaShieldHalved,
  FaStar,
  FaStore,
  FaTruck,
} from "react-icons/fa6";


// This page is used as show case using the UI with some placeholder data.
function ProductPage() {
  const [selectedColor, setSelectedColor] = useState("زرد");

  // clicked product image modal
  const [openedImageSrc, setOpenedImageSrc] = useState<string | null>(null);
  const imageModalRef = useRef<HTMLDialogElement>(null);

  const selectedColorObj = colors.find((color) => color.name === selectedColor);

  // For closing the opened image by clicking outside the box.
  const handleModalOutsideClose = (
    e: React.MouseEvent<HTMLDialogElement, MouseEvent>
  ) => {
    const dialog = imageModalRef.current;
    if (imageModalRef.current && e.target == dialog) {
      setOpenedImageSrc(null);
    }
  };

  // When opened image state gets changed, using its ref,
  // open or close the image based on state's value
  useEffect(() => {
    if (openedImageSrc) {
      imageModalRef.current?.showModal();
    } else {
      imageModalRef.current?.close();
    }
  }, [openedImageSrc]);

  return (
    <>
      <div className="lg:px-4 max-w-(--breakpoint-2xl)">
        {openedImageSrc && (
          <dialog
            ref={imageModalRef}
            className="modal"
            onCancel={() => setOpenedImageSrc(null)}
            onClick={handleModalOutsideClose}
            id="image_modal"
          >
            <div className="modal-box">
              <form method="dialog" className="modal-backdrop ">
                <button
                  onClick={() => setOpenedImageSrc(null)}
                  className="btn btn-sm btn-circle absolute"
                >
                  ✕
                </button>
              </form>
              <Image
                src={openedImageSrc}
                width={450}
                height={450}
                alt="product"
                className="place-self-center"
              />
            </div>
          </dialog>
        )}
        <div className="justify-items m-2 w-full">
          <div className="flex flex-col lg:flex-row">
            <div className="card grid basis-3/6 place-items-center lg:ml-2 mb-2 ">
              <Image
                className="mask lg:w-9/12 w-3/6 rounded-2xl pb-4"
                src="/sample_images/product-main-image.webp"
                alt="Laptop"
                width={1000}
                height={1000}
              />
              <div className="flex self-start pb-1 gap-3 scrollbar overflow-x-auto scrollbar-thumb-rounded-full scrollbar-track-rounded-full scrollbar-thumb-slate-700 scrollbar-track-slate-300">
                <ProductImage
                  images={images}
                  onClickEventHandler={setOpenedImageSrc}
                />
              </div>
            </div>
            <div>
              <div className="card bg-base-200 rounded-box min-h-16 max-h-48 basis-2/3 p-3 lg:mx-0">
                <span className="text-sm font-normal pb-2">
                  <a className="text-blue-400" href="#">
                    وسایل التکرونیکی
                  </a>
                  <span> / </span>
                  <a href="#" className="text-blue-400">
                    لپتاپ
                  </a>
                </span>
                <h1 className="text-lg leading-8 font-medium">
                  لپ تاپ 15.6 اینچی اچ‌ پی مدل Victus 15 Gaming FB2082wm-R5
                  8645HS-64GB DDR5-1TB SSD-RTX4050-FHD-W - کاستوم شده
                </h1>
              </div>
              <div className="grid grid-rows-[auto_1fr] lg:grid-cols-[8fr_5fr] grid-cols-[1fr_2fr] my-3 wrap gap-4">
                <div className="lg mx-4">
                  <div className="flex gap-1">
                    <FaStar className=" text-yellow-300" />
                    <p className="font-light text-sm">
                      4.1 امتیاز ( از 214 خریدار)
                    </p>
                  </div>
                  <ProductColor
                    colors={colors}
                    selectedColor={selectedColor}
                    setSelectedColor={setSelectedColor}
                  />
                </div>
                <div className="card h-fit lg:w-full w-8/12 min-w-64 max-w-96 shadow-xl bg-base-200 mr-auto font-medium text-sm col-span-1 row-span-2 ">
                  <div className="card-body p-5 flex flex-col gap-3">
                    <h2 className="card-title">فروشنده</h2>
                    <div className="flex gap-2 border-b-[1px] pb-2 border-base-300">
                      <FaStore className="text-xl text-orange-400" />
                      <p>فروشگاه تک سینا</p>
                    </div>
                    <div className="flex justify-between my-1 font-medium ">
                      <span>قیمت</span>
                      <span>{selectedColorObj?.price} تومان</span>
                    </div>
                    <div className="flex gap-2 text-xl border-b-[2px] pb-2 border-base-300">
                      <FaShieldHalved className="text-blue-400" />
                      <p className="text-sm"> گارانتی 24 ماهه آوا</p>
                    </div>
                    <div className="flex gap-2 ">
                      <FaCheck className=" text-green-600 text-xl" />
                      <p>شامل ضمانت 7 روزه</p>
                    </div>
                    <div className="card-actions justify-center">
                      <button className="btn btn-primary mt-2 w-full">
                        افزودن به سبد خرید
                      </button>
                    </div>
                  </div>
                </div>
                <div className=" lg:col-span-1 col-span-2 ">
                  <h2 className="font-semibold text-lg mt-2 mb-1">ویژگی ها</h2>
                  <div className="lg:grid grid-cols-3 flex gap-4 w-full lg:overflow-hidden overflow-scroll scrollbar-thumb-rounded-full scrollbar-track-rounded-full scrollbar-thumb-slate-700 scrollbar-track-slate-300 py-1">
                    <ProductFeature
                      name={"نسل پردازنده"}
                      value={"نسل 8 ای ام دی"}
                    />
                    <ProductFeature name={"سری پردازنده"} value={"Ryzen 5"} />
                    <ProductFeature name={"ظرفیت حافظه RAM"} value={"16GB"} />
                    <ProductFeature
                      name={"سازنده پردازنده گرافیکی"}
                      value={"NVIDIA"}
                    />
                    <ProductFeature
                      name={"رزولوشن صفحه نمایش"}
                      value={"1920x1080"}
                    />
                    <ProductFeature
                      name={"نرخ بروز رسانی تصویر"}
                      value={"144 هرتز"}
                    />
                    <ProductFeature name={"نسخه ی بلوتوث"} value={"5.3"} />
                    <ProductFeature
                      name={"مدل پردازنده گرافیکی"}
                      value={"GeForce RTX 4050"}
                    />
                    <ProductFeature
                      name={"اندازه صفحه نمایش"}
                      value={"15.6 اینچ"}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="flex gap-16 max-w-(--breakpoint-2xl)  place-self-center justify-between border-y-2 border-base-300 p-4 px-8 mt-8 w-full">
          <div className="bg-base flex flex-col items-center gap-2 ">
            <FaHeadset className="text-4xl" />
            <p>پشتیبانی 24 ساعته</p>
          </div>
          <div className="bg-base flex flex-col items-center gap-2">
            <FaCreditCard className="text-4xl" />
            <p> امکان پرداخت در محل </p>
          </div>
          <div className="bg-base flex flex-col items-center gap-2">
            <FaTruck className="text-4xl" />
            <p>تحویل به موقع</p>
          </div>
          <div className="bg-base flex flex-col items-center gap-2">
            <FaCalendarCheck className="text-4xl" />
            <p>7 روز ضمانت بازگشت کالا</p>
          </div>
        </div>
        <div
          role="tablist"
          className="tabs tabs-lifted place-self-center w-full my-8 shadow-lg"
        >
          <input
            type="radio"
            name="my_tabs_2"
            role="tab"
            className="tab"
            aria-label="مشخصات"
          />
          <div
            role="tabpanel"
            className="tab-content bg-base-100 border-secondary rounded-box p-6 border-r-8 "
          >
            <ProductDetail details={details} />
          </div>

          <input
            type="radio"
            name="my_tabs_2"
            role="tab"
            className="tab"
            aria-label="معرفی"
            defaultChecked
          />
          <div
            role="tabpanel"
            className="tab-content bg-base-100 border-r-8 border-primary from-base-200 to-base-300 rounded-box p-6 "
          >
            <p className="max-w-(--breakpoint-2xl) leading-7 text-sm font-medium">
              اچ پی با سری Victus، لپ‌تاپ‌هایی با سخت‌افزار قدرتمند و طراحی شیک
              و ساده عرضه می‌کند تا نیاز کاربران برای پردازش‌های سنگین و البته
              بازی کردن را برطرف کند. لپ‌تاپ Victus Gaming 15 به عنوان یکی از
              گزینه‌های میان رده‌ی این سری معرفی شده که ضمن برخورداری از
              سخت‌افزار به‌روز و قدرتمند، قیمت مناسبی دارد. وزن 2.3 کیلوگرمی و
              ابعاد 15.6 اینچی با توجه به سخت‌افزار استفاده شده قابل قبول است و
              در زمان جابجایی چندان مشکل ساز نخواهد بود. صفحه‌نمایش از پنل با
              کیفیت IPS استفاده می‌کند و وضوح 1920 در 1080 یا همان Full HD دارد.
              نرخ به‌روزرسانی 144 هرتزی تجربه‌ای روان و لذت بخش در هنگام بازی‌
              کردن به همراه دارد. پردازنده‌ی Ryzen 5 نسل 8 از AMD، با استفاده از
              6 هسته و 12 رشته پردازشی و حداکثر فرکانس 5 گیگاهرتزی، خیال کاربر
              از تجربه‌ی بدون لگ را راحت کرده و به خوبی از پس وظایف خود
              برمی‌آید. در بخش گرافیک، پردازنده Geforce RTX 4050 با شش گیگابایت
              حافظه اختصاصی GDDR6 از قدرت کافی برای اجرای برنامه‌ها و بازی‌های
              سنگین با کیفیت خوب و نرخ فریم مناسب برخوردار است و در مواقعی از
              فناوری کاربردی DLSS برای بهبود عملکرد و افزایش فریم خروجی بهره
              می‌گیرد. استفاده از حافظه رم DDR5 با فرکانس 5600 مگاهرتز در کنار
              پردازنده مرکزی کمک می‌کند تا اجرای برنامه‌ها به صورت همزمان و
              جابجایی سریع بین آن‌ها ممکن باشد. برای ذخیره اطلاعات هم حافظه‌ی
              پرسرعت SSD در نظر گرفته شده که در مقایسه با هارددیسک‌های قدیمی،
              سرعت به مراتب بالاتری در بارگذاری‌ها و جابجایی فایل‌ نشان می‌دهد.
              طراحی شیک و ساده، باتری 4 سلولی با ظرفیت 70 وات ساعت و نور
              پس‌زمینه کیبورد از دیگر ویژگی‌های Victus Gaming 15 به شمار
              می‌آیند.
            </p>
          </div>

          <input
            type="radio"
            name="my_tabs_2"
            role="tab"
            className="tab "
            aria-label="نظرات"
          />
          <div
            role="tabpanel"
            className="tab-content bg-base-100 border-accent border-r-8 rounded-box p-8 text-red-500 font-bold text-2xl"
          >
            <h1>این بخش غیر فعال می باشد.🙂</h1>
          </div>
        </div>
      </div>
    </>
  );
}

export default ProductPage;
