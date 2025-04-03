import { fetchBreadCrumb } from "../lib/fetch/product-list/fetch-product-list";
import { isError } from "../lib/fetch/fetchWrapper";

export default async function CategoryBreadcrumb({
  subCategoryId,
}: {
  subCategoryId: number;
}) {
  // fetch breadcrumb data
  const categoryBreadCrumbResult = await fetchBreadCrumb(subCategoryId);

  return isError(categoryBreadCrumbResult) ? (
    <div className="text-sm pt-2 pb-1">
      <p className="text-error font-semibold italic">
        {" "}
        خطا در دریافت بردکرامپ ⚠️{" "}
      </p>
    </div>
  ) : (
    <div className="breadcrumbs text-sm pt-2 pb-1">
      <ul>
        <li>
          <a>{categoryBreadCrumbResult.mainCategory}</a>
        </li>
        <li>
          <a>{categoryBreadCrumbResult.category}</a>
        </li>
        <li>
          <a>{categoryBreadCrumbResult.subCategory}</a>
        </li>
      </ul>
    </div>
  );
}
